from django.shortcuts import render, redirect
from .forms import ContactForm
from .models import Tag, Contact
from .forms import TagForm
from django.shortcuts import render, redirect
import pandas as pd
from django.http import HttpResponse

def index(request):
    return render(request, 'main/index.html')
# def add_contact(request):
#     if request.method == 'POST':
#         form = ContactForm(request.POST)
#         if form.is_valid():
#             contact = form.save(commit=False)
#             contact.user = request.user
#             contact.save()
#             return redirect('contacts_list')
#     else:
#         form = ContactForm()
#     return render(request, 'main/add_contact.html', {'form': form})

def tag_list(request):
    tags = Tag.objects.all()
    return render(request, 'main/tag_list.html', {'tags': tags})

def add_tag(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tag_list')
    else:
        form = TagForm()
    return render(request, 'main/add_tag.html', {'form': form})

def search_contacts(request):
    query = request.GET.get('q', '')
    contacts = Contact.objects.filter(
        first_name__icontains=query
    ) | Contact.objects.filter(
        last_name__icontains=query
    )
    return render(request, 'main/search_results.html', {'contacts': contacts, 'query': query})

# def export_contacts_csv(request):
#     contacts = Contact.objects.all().values()
#     df = pd.DataFrame(contacts)
#     response = HttpResponse(content_type='text/csv')
#     response['Content-Disposition'] = 'attachment; filename="contacts.csv"'
#     df.to_csv(path_or_buf=response, index=False)
#     return response

# def import_contacts_csv(request):
#     if request.method == 'POST':
#         csv_file = request.FILES['file']
#         df = pd.read_csv(csv_file)
#         for _, row in df.iterrows():
#             Contact.objects.create(
#                 first_name=row['first_name'],
#                 last_name=row['last_name'],
#                 company_name=row.get('company_name', ''),
#                 address=row.get('address', ''),
#                 phone=row.get('phone', ''),
#                 email=row.get('email', ''),
#                 comment=row.get('comment', '')
#             )
#         return redirect('contact_list')
#     return render(request, 'main/import_contacts.html')

def create_tag(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tag_list')
    else:
        form = TagForm()
    return render(request, 'create_tag.html', {'form': form})

def contacts_list(request):
    contacts = Contact.objects.all()
    return render(request, 'contacts_list.html', {'contacts': contacts})

def search_contacts(request):
    query = request.GET.get('q')
    if query:
        contacts = Contact.objects.filter(first_name__icontains=query) | Contact.objects.filter(last_name__icontains=query)
    else:
        contacts = Contact.objects.all()
    return render(request, 'contacts_list.html', {'contacts': contacts})


import pandas as pd
from django.http import HttpResponse


def import_contacts(request):
    if request.method == 'POST' and request.FILES['csv_file']:
        file = request.FILES['csv_file']
        df = pd.read_csv(file)

        for _, row in df.iterrows():
            contact = Contact.objects.create(
                first_name=row['first_name'],
                last_name=row['last_name'],
                email=row['email'],
                phone=row['phone'],
                address=row['address']
            )
            contact.save()

        return HttpResponse("Контактите бяха импортирани успешно!")
    return render(request, 'import_contacts.html')

def export_contacts(request):
    contacts = Contact.objects.all()
    df = pd.DataFrame(list(contacts.values()))
    response = HttpResponse(df.to_csv(index=False), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="contacts.csv"'
    return response
def create_contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()  # Записваме новия контакт в базата данни
            return redirect('contacts_list')  # Пренасочваме към списъка с контакти
    else:
        form = ContactForm()

    return render(request, 'main/create_contact.html', {'form': form})



