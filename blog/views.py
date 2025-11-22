from django.shortcuts import render
from django.http import HttpResponse
from math import ceil
from .models import BlogPost

# Create your views here.
def index(request):
    myposts = BlogPost.objects.all()
    print(myposts)

    # Divide the products into rows of 4
    n = len(myposts)
    nSlides = n // 4 + ceil((n / 4) - (n // 4))
    posts = [myposts[i:i + 4] for i in range(0, n, 4)]  # Fix the range
    params = {'posts': posts}
    # print(params)
    return render(request , 'blog/index.html',params)

def blogpost(request,id):
    mypost = BlogPost.objects.filter(post_id=id)
    print(mypost)
    return render(request , 'blog/blogpost.html' , {'post':mypost} )


 