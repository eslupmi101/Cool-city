from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CreationForm, EmailResetPassword


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('posts:index')
    template_name = 'users/signup.html'


def password_reset_form(request):
    template = 'users/password_reset_form.html'
    form = EmailResetPassword()
    if request.method == 'POST':
        form = EmailResetPassword(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            if User.objects.filter(email=email).count():
                send_mail(
                    'Тема письма',
                    'Текст письма',
                    'from@example.com',
                    [email],
                    fail_silently=False,
                )
            return redirect('users:password_reset_done')
    return render(request, template, {'form': form})
