from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from .models import Module
from pytube import YouTube,extract
from youtube_transcript_api import YouTubeTranscriptApi
import torch
import sentencepiece
from transformers import T5Tokenizer, T5ForConditionalGeneration, T5Config,AutoTokenizer

# Create your views here.

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return render(request,'home.html')


def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request,'Email Taken')
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request,'Username Taken')
                return redirect('signup')
            else:
                user = User.objects.create_user(username=username,email=email,password=password)
                user.save()
                return redirect('dashboard')
        else:
            messages.info(request,'Passwords not matching')
            return redirect('signup')

    return render(request,'signup.html')

def userlogin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username,password=password)

        if user is not None:
            login(request,user)
            return redirect('dashboard')
        else :
            messages.info(request,'Invalid Login Details')
            return redirect('login')

    return render(request,'login.html')


def userlogout(request):
    logout(request)
    return redirect('login')

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
      # Creating a New Module
      title = request.POST['title']
      description = request.POST['description']
      videosList = []
      # Checking if the title is unique
      if Module.objects.filter(title=title).exists():
        messages.info(request,'Module Title Taken')
        return redirect('dashboard')
      else:
        Module.objects.create(title=title,description=description,videosList=videosList)
        return redirect(reverse('module', args=(title,)))
    else:
        # Retriving all the existing modules for the database
        modules = Module.objects.all().values()
        return render(request,'dashboard.html',{'modules':modules})


def module(request,moduleName):
    if not request.user.is_authenticated:
        return redirect('login')
    # Getting the specific module name which is coming as a string
    if request.method == "POST":
        url = request.POST['url']
        yt = YouTube(url)
        videoId = extract.video_id(url)
        embedUrl = "https://www.youtube.com/embed/" + videoId
        jsonObject = {
            "title":yt.title,
            "videoId":videoId,
            "embedUrl":embedUrl,
            "isCompleted":False,
            "notes":[]
        }
        moduleObject = Module.objects.filter(title=moduleName).get()
        datalist = moduleObject.videosList
        datalist.append(jsonObject)
        moduleObject.videosList = datalist
        moduleObject.save()
        return redirect(reverse('module', args=(moduleName,)))
    data = Module.objects.filter(title=moduleName).values('description','videosList')
    modifiedData = list(data)
    # Get the progress percentage
    total = len(modifiedData[0]['videosList'])
    completed = 0
    for videoData in modifiedData[0]['videosList']:
        if videoData['isCompleted']==True:
            completed = completed+1
    return render(request,'module.html',{'title':moduleName,'description':modifiedData[0]['description'],'videosList':modifiedData[0]['videosList'],'total':total,'completed':completed})

def video(request,moduleName,videoId):
    if not request.user.is_authenticated:
        return redirect('login')
    # Get the particular video object
    moduleObject = Module.objects.filter(title=moduleName).get()
    datalist = moduleObject.videosList
    videoObject = None
    summary_text = ""
    for videoData in datalist:
        if videoData['videoId']==videoId:
            videoObject = videoData
    if request.method == 'POST':
        if 'mark-done' in request.POST:
            jsonObject = {
                "title":videoObject['title'],
                "videoId":videoId,
                "embedUrl":videoObject['embedUrl'],
                "isCompleted":True,
                "notes":videoObject['notes']
            }
            tempObject = videoObject
            datalist.remove(tempObject)
            datalist.append(jsonObject)
            moduleObject.videosList = datalist
            moduleObject.save()
            return redirect(reverse('module', args=(moduleName,)))
        elif 'remove-video' in request.POST:
            tempObject = videoObject
            datalist.remove(tempObject)
            moduleObject.videosList = datalist
            moduleObject.save()
            return redirect(reverse('module', args=(moduleName,)))
        elif 'note-add' in request.POST:
            note = request.POST['note']
            notesList = videoObject['notes']
            notesList.append(note)
            jsonObject = {
                "title":videoObject['title'],
                "videoId":videoId,
                "embedUrl":videoObject['embedUrl'],
                "isCompleted":False,
                "notes":notesList
            }
            datalist.append(jsonObject)
            moduleObject.videosList = datalist
            moduleObject.save()
            return redirect(reverse('video', args=(moduleName,videoId,)))
        elif 'transcript' in request.POST:
            transcript = ""
            transcriptList = YouTubeTranscriptApi.get_transcript(videoObject['videoId'])
            for index in transcriptList:
                transcript = transcript + index['text']
            return render(request,'video.html',{"videoObject":videoObject,"title":moduleName,"transcript":transcript})
        elif 'summary' in request.POST:
            transcript = ""
            transcriptList = YouTubeTranscriptApi.get_transcript(videoObject['videoId'])
            for index in transcriptList:
                transcript = transcript + index['text']
            # Summarisation the transcript
            summary_text = summarise(transcript)
            return render(request,'video.html',{"videoObject":videoObject,"title":moduleName,"summary":summary_text})
    
    return render(request,'video.html',{"videoObject":videoObject,"title":moduleName})

def summarise(text):
    output = None
    try:
        model = T5ForConditionalGeneration.from_pretrained('t5-small')
        tokenizer = T5Tokenizer.from_pretrained('t5-small')
        device = torch.device('cpu')
        preprocess_text = text.strip().replace("\n","")
        t5_prepared_Text = "summarize: "+preprocess_text
        tokenized_text = tokenizer.encode(t5_prepared_Text, return_tensors="pt",truncation=True).to(device)
        # summmarize 
        summary_ids = model.generate(tokenized_text,
                                    num_beams=4,
                                    no_repeat_ngram_size=2,
                                    min_length=30,
                                    max_length=3000,
                                    early_stopping=True)

        output = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    except TypeError:
        output = "Unable to generate summary currently"
    return output

    

