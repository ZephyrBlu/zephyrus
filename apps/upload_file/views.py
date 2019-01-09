from django.shortcuts import render, reverse, redirect
from .forms import ReplayFileForm
from django.core.validators import FileExtensionValidator
from django.views.generic.edit import FormView
from apps.processreplays.views import parse_replay

# class ReplayFileFormView(FormView):
#     form_class = ReplayFileForm
#     template_name = 'upload_file/upload_form.html'  # Replace with your template.
#     success_url = 'home/'  # Replace with your URL or reverse().
#
#     def post(self, request, *args, **kwargs):
#         form_class = self.get_form_class()
#         form = self.get_form(form_class)
#         files = request.FILES.getlist('file')
#         if form.is_valid():
#             for f in files:
#                 file_extension_checker = FileExtensionValidator(['sc2replay'])
#                 file_extension_checker(f.name)
#             return self.form_valid(form)
#         else:
#             return self.form_invalid(form)

def upload_form(request, context):
    if request.method == 'POST':
        form = ReplayFileForm(request.POST, request.FILES)
        if form.is_valid():
            file_extension_checker = FileExtensionValidator(['sc2replay'])
            file_extension_checker(request.FILES['file'])
            form.save()
            return redirect('/profile/')
    else:
        form = ReplayFileForm()
        context['form'] = form
    return render(request, 'upload_file/upload_form.html', context)
