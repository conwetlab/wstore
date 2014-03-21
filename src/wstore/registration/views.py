from django.contrib import messages
from django.contrib.auth import login
from django.http import HttpResponseNotFound
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import FormView

from wstore.registration.forms import RegistrationForm
from wstore.registration.models import Profile


class RegistrationView(FormView):
    """
    """
    http_method_names = ['head', 'get', 'post']
    template_name = 'registration/signup_template.html'
    form_class = RegistrationForm

    def form_valid(self, form):
        """
        """
        new_user = form.save()
        self.create_success_message(new_user)
        return self.render_to_response(
            self.get_context_data(form=form, success=True))

    def create_success_message(self, user):
        """
        """
        message = _("WStore has sent an activation e-mail to %s."
                    "Please, check it out.") % (user.email)
        messages.success(self.request, message)


signup_view = RegistrationView.as_view()


@require_http_methods(["GET"])
def activate_view(request, activation_key):
    """
    """
    user = Profile.objects.activate_user(activation_key)
    if user:
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        message = _("Well done! You can use WStore.")
        messages.success(request, message)
        return redirect('home')
    return HttpResponseNotFound('<h1>Page not found</h1>')
