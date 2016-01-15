from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.template.context_processors import csrf
from accounts.forms import UserRegistrationForm, UserLoginForm
from django.core.mail import EmailMessage
from django.conf import settings
import stripe
import datetime

stripe.api_key = settings.STRIPE_SECRET

'''**Initial register function**

def register(request, register_form=UserRegistrationForm):
    if request.method == 'POST':
        form = register_form(request.POST)
        if form.is_valid():
            form.save()
            user = auth.authenticate(email=request.POST.get('email'),
                                     password=request.POST.get('password1'))
            if user:
                messages.success(request, "You have successfully registered")
                email = EmailMessage('Confirmation', 'This is a confirmation email')
                email.send()
                return redirect(reverse('login'))
            else:
                messages.error(request, 'unable to log you in at this time!')
    else:
        form = register_form()
    args = {'form': form}
    args.update(csrf(request))
    return render(request, 'register.html', args)

    **Initial register function'''


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():

            try:
                customer = stripe.Charge.create(
                    amount=499,
                    currency='USD',
                    description=form.cleaned_data['email'],
                    card=form.cleaned_data['stripe_id'],
                )
            except stripe.error.CardError, e:
                messages.error(request, "Your card was declined!")

            if customer.paid:
                form.save()

                user = auth.authenticate(email=request.POST.get('email'),
                                         password=request.POST.get('password1'))

                if user:
                    auth.login(request, user)
                    messages.success(request, "You have successfully registered")
                    return redirect(reverse('profile'))

            else:
                messages.error(request, "unable to log you in at this time!")
        else:
            messages.error(request, "We were unable to take a payment with that card!")

    else:
        today = datetime.date.today()
        form = UserRegistrationForm(initial={'expiry_month': today.month,
                                             'expiry_year': today.year})

    args = {'form': form, 'publishable': settings.STRIPE_PUBLISHABLE}
    args.update(csrf(request))

    return render(request, 'register.html', args)


def login(request, success_url=None):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = auth.authenticate(email=request.POST.get('email'),
                                     password=request.POST.get('password'))

            if user is not None:
                auth.login(request, user)
                messages.error(request, "You have successfully logged in")
                return redirect(reverse('profile'))
            else:
                form.add_error(None, "Your email or password was not recognised")
        else:
            return render(request, 'contact.html', {'form': form})
    else:
        form = UserLoginForm()

        args = {'form': form}
        args.update(csrf(request))
        return render(request, 'login.html', args)


@login_required(login_url='/accounts/login/')
def profile(request):
    return render(request, 'profile.html')


def logout(request):
    auth.logout(request)
    messages.success(request, 'You have successfully logged out')
    return render(request, 'index.html')
