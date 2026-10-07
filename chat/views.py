from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Create your views here.
def index(request):
    return render(request, 'chat/index.html')

# chat room page
@login_required(login_url='login')
def room(request, room_name):
    return render(request, 'chat/room.html', {'room_name': room_name})