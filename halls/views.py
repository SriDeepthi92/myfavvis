from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.forms import UserCreationForm
from .models import Hall, Video
from django.contrib.auth import authenticate, login
from .forms import VideoForm, SearchForm
from django.http import Http404, JsonResponse
from django.forms.utils import ErrorList
import urllib
import requests
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

YOUTUBE_API_KEY = 'AIzaSyAJPcO-PsgVZuggw0EwMQr-K_SLPB5oas8'
TMDB_API_KEY = 'c170e51ce0b1532553de58afa5e61281'
base_url = 'https://api.themoviedb.org/3/'

def home(request):
    #recent_halls = Hall.objects.all().order_by('-id')[:3]
    #popular_halls = [Hall.objects.get(pk=1),Hall.objects.get(pk=2),Hall.objects.get(pk=3)]
    return render(request, 'halls/home.html')

def index(request):
	context = {}
	categories = ['now_playing', 'upcoming', 'popular', 'top_rated']

	try:
		for category in categories:
			endpoint = 'https://api.themoviedb.org/3/movie/{category}?api_key=c170e51ce0b1532553de58afa5e61281&language=en-US&page=1'
			url = endpoint.format(category=category, api_key=settings.TMDB_API_KEY)
			response = requests.get(url)
			context[category] = response.json()

	except:
		context['success'] = False
		context['message'] = 'Connection To TMDB API not available at the moment, Check Your Internet Connection and Try again later'


	return render(request, 'halls/index.html', context)

def detail(request):
	movie_detail = {}

	try:
		endpoint = 'https://api.themoviedb.org/3/movie/{movie_id}?api_key=c170e51ce0b1532553de58afa5e61281&language=en-US&append_to_response=videos'
		url = endpoint.format(movie_id=id, api_key=settings.TMDB_API_KEY)
		response = requests.get(url)
		movie_detail = response.json()
		movie_detail['success'] = True
	except:
		movie_detail['success'] = False
		movie_detail['message'] = 'Connection To TMDB API not available at the moment, Check Your Internet Connection and Try again later'

	return render(request, 'halls/details.html', {'movie_detail': movie_detail})


def search(request):
	result = {}
	if 'q' in request.GET:
		query = request.GET['q']

		try:
			endpoint = 'https://api.themoviedb.org/3/search/movie?api_key=c170e51ce0b1532553de58afa5e61281&query={query}'
			url = endpoint.format(api_key = settings.TMDB_API_KEY, query = query)
			response = requests.get(url)
			result = response.json()
			result['searched_item'] = query
			result['success'] = True
		except:
			result['searched_item'] = query
			result['message'] = 'Connection to TMDB API not Available at the moment try again later'
			result['success'] = False
	return render(request, 'halls/result.html', {'result': result})


def movies(request):
    url = f'{base_url}movie/upcoming?api_key={TMDB_API_KEY}&language=en-US&page=1'

    response = requests.get(url)
    movies = response.json()['results']
    context = {
        'title': 'Upcoming',
        'movies': movies,
    }
    return render(request, 'halls/movies.html', context)

@login_required
def dashboard(request):
    halls = Hall.objects.filter(user=request.user)
    return render(request, 'halls/dashboard.html', {'halls':halls})

#def wiki(request):
    #page = urllib.parse.parse_qs(parsed_url.query).get('page')
    #if 'video.title' in request.GET:
    #    username = request.GET['username']
    #    response = requests.get(f'https://en.wikipedia.org/w/api.php?action=parse&page={ video.title }&prop=wikitext&formatversion=2')
    #    user = response.json()

    #return render(request, 'halls/details.html', {
    #    'ip': geodata['ip'],
    #    'country': geodata['country_name'],
    #    'latitude': geodata['latitude'],
    #    'longitude': geodata['longitude'],
    ##    'api_key': 'AIzaSyC1UpCQp9zHokhNOBK07AvZTiO09icwD8I',  # Don't do this! This is just an example. Secure your keys properly.
    #    'is_cached': is_cached
    #})

def detail_search(request):
    wiki_form = wikiForm(request.GET)
    if wiki_form.is_valid():
        encoded_wiki_term = urllib.parse.quote(wiki_form.cleaned_data['wiki_term'])
        response = requests.get(f'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={ encoded_wiki_term }a&utf8=&format=json')
        return JsonResponse(response.json())
    return JsonResponse({'error':'Not able to validate form'})

def add_video(request, pk):
    form = VideoForm()
    search_form = SearchForm()
    hall = Hall.objects.get(pk=pk)
    if not hall.user == request.user:
        raise Http404
    if request.method == 'POST':
            form = VideoForm(request.POST)
            if form.is_valid():
                video = Video()
                video.hall = hall
                video.url = form.cleaned_data['url']
                parsed_url = urllib.parse.urlparse(video.url)
                video_id = urllib.parse.parse_qs(parsed_url.query).get('v')
                if video_id:
                    video.youtube_id = video_id[0]
                    response = requests.get(f'https://youtube.googleapis.com/youtube/v3/videos?part=snippet&id={ video_id[0] }&key={ YOUTUBE_API_KEY }')
                    json = response.json()
                    title = json['items'][0]['snippet']['title']
                    video.title = title
                    video.save()
                    return redirect('detail_hall', pk)
                else:
                    errors = form._errors.setdefault('url', ErrorList())
                    errors.append('Needs to be a YouTube URL')

    return render(request, 'halls/add_video.html', {'form':form, 'search_form':search_form})

@login_required
def video_search(request):
    search_form = SearchForm(request.GET)
    if search_form.is_valid():
        encoded_search_term = urllib.parse.quote(search_form.cleaned_data['search_term'])
        response = requests.get(f'https://youtube.googleapis.com/youtube/v3/search?part=snippet&maxResults=5&q={ encoded_search_term }&key={ YOUTUBE_API_KEY }')
        return JsonResponse(response.json())
    return JsonResponse({'error':'Not able to validate form'})

def details(request,id):
    response=requests.get(f'https://api.themoviedb.org/3/search/movie?api_key = { TMDB_API_KEY } &language=en-US&query={ encoded_search_term }&page=1&include_adult=false')
    data=response.json()
    return render(request,'detail.html',{"data":data})


class DeleteVideo(generic.DeleteView):
    model = Video
    template_name = 'halls/delete_video.html'
    success_url = reverse_lazy('dashboard')

    def get_object(self):
        video = super(DeleteVideo, self).get_object()
        if not video.hall.user == self.request.user:
            raise Http404
        return video

class SignUp(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('dashboard')
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        view = super(SignUp, self).form_valid(form)
        username, password = form.cleaned_data.get('username'), form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return view


class CreateList(generic.CreateView):
    model = Hall
    fields = ['title']
    template_name = 'halls/create_list.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.user = self.request.user
        super(CreateList, self).form_valid(form)
        return redirect('dashboard')

class UpdateList(LoginRequiredMixin,generic.UpdateView):
    model = Hall
    template_name = 'halls/update_list.html'
    fields = ['title']
    success_url = reverse_lazy('dashboard')

    def get_object(self):
        hall = super(UpdateList, self).get_object()
        if not hall.user == self.request.user:
            raise Http404
        return hall

class DeleteList(LoginRequiredMixin,generic.DeleteView):
    model = Hall
    template_name = 'halls/delete_list.html'
    success_url = reverse_lazy('dashboard')

    def get_object(self):
        hall = super(DeleteHall, self).get_object()
        if not hall.user == self.request.user:
            raise Http404
        return hall

class DetailHall(generic.DetailView):
    model = Hall
    template_name = 'halls/detail_hall.html'
