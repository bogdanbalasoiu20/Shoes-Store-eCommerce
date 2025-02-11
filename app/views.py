from django.shortcuts import render,redirect
from .models import Product, Brands, Category, CustomUser,Offer,Views, ProductSizeStock,Size, Order, OrderProduct
from .forms import ProductForm, ContactForm,ProductForm2,CustomUserForm,CustomAuthentificationForm,PromotionsForm
from django.core.paginator import Paginator
import os
import time
from django.utils import timezone
import json
import datetime
from django.utils.timezone import now
from django.contrib.auth import login,logout
from django.http import HttpResponse,HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.utils.crypto import get_random_string 
from django.core.mail import mail_admins
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMessage,send_mass_mail
import logging
from django.shortcuts import get_object_or_404
from django.db.models import Count
from django.utils.html import strip_tags
from django.contrib.auth.models import Permission
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from decimal import Decimal


logger=logging.getLogger('django') #creez un logger


def test(request):
    return HttpResponse("server is running")



def product_list(request):
    #imi iau obiectele din baza de date(queryset-ul initial)
    products = Product.objects.all()
    
    active_offers = Offer.objects.filter(
        start_date__lte=timezone.now().date(),
        end_date__gte=timezone.now().date()
        ).prefetch_related('product')
            
        
    
    if request.method=='POST':
        form=ProductForm(request.POST)
        #daca formularul este validat, preiau datele din dictionarul cleaned_data in functie de valoarea cheii
        if form.is_valid():
            name=form.cleaned_data.get("name")
            #filtrez in functie de nume(__icontains cauta o potrivire partiala in campul text, nu tine cont de majuscule)
            if name:
                products=products.filter(name__icontains=name)
                
            #descriere
            description=form.cleaned_data.get("description")
            if description:
                products=products.filter(description__icontains=description)
                
            #price range
            price_min=form.cleaned_data.get("price_min")
            price_max=form.cleaned_data.get("price_max")
            if price_min:
                products=products.filter(price__gte=price_min)
            if price_max:
                products=products.filter(price__lte=price_max)
                
            #brand filter
            brand=form.cleaned_data.get("brand")
            if brand and brand != Brands.none and brand != Brands.unknown:
                products=products.filter(brand=brand)
                
            #category filter
            category=form.cleaned_data.get("category")
            if category and category!= Category.none:
                products=products.filter(category=category)
                
            #supplier filter
            supplier=form.cleaned_data.get("supplier")
            if supplier:
                products=products.filter(supplier=supplier)
                
            # Filtrare după mărime cu stoc > 0
            size = form.cleaned_data.get("size")
            if size:
                products = products.filter(
                    id__in=ProductSizeStock.objects.filter(size=size, stock__gt=0).values_list('product_id', flat=True)
                )
    else:
        form=ProductForm() #daca nu, transmit un formular gol
            
    #product pagination
    paginator=Paginator(products.order_by('id'),10)
    page_number=request.GET.get('page')
    page_obj=paginator.get_page(page_number) #creeaza o instanta de pagina care contine elementele corespunzatoare paginii cu numarul page_number, page_obj contine date despre pagina curenta
    
    
    product_data = []

    for product in page_obj.object_list:
        
        sizes=ProductSizeStock.objects.filter(product=product).order_by('size__size').values_list('size__size',flat=True)
        
        product_info = {
            'product': product,
            'offers': [],
            'old_price': product.price,
            'new_price': product.price,
            'size':sizes
        }

        for offer in active_offers:
            if product in offer.product.all() or product.category.lower() in [cat.name.lower() for cat in offer.category.all()]:
                product_info['offers'].append(offer.name)
                if offer.discount_type == 'percentage':
                    product_info['new_price'] *= (1 - offer.discount_value / 100)
                elif offer.discount_type == 'fixed_amount':
                    product_info['new_price'] = max(0, product_info['new_price'] - offer.discount_value)
        
        product_data.append(product_info)
        
    
    return render(request,'product_list.html',{'form':form, 'page_obj':page_obj,'product_data':product_data})    


def add_view(user,product):
    is_product=Views.objects.filter(user=user,product=product).exists() #verific daca vizualizare pentru un produs nu apare deja in dreptul aceluiasi user in tabel
    if not is_product: 
        Views.objects.create(user=user,product=product,view_date=now()) #pentru fiecare produs creez o vizualizare
        
    views=Views.objects.filter(user=user).order_by('-view_date') #filtrez obiectele in functie de user-ul autentificat si le sortez crescator
    N=5 #limita de vizualizari
    if views.count()>N:   
        view_to_delete=views.last()
        view_to_delete.delete()
        
    #daca am mai mult de N vizualizari, sterg cea mai veche vizualizare
 

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.user.is_authenticated:
        add_view(request.user, product)  # Înregistrez doar produsul curent
    
    active_offers = Offer.objects.filter(
        start_date__lte=timezone.now().date(),
        end_date__gte=timezone.now().date()
    ).prefetch_related('product')
    
    offers = []
    price_after_offer = product.price
    for offer in active_offers:
        if product in offer.product.all() or product.category.lower() in [cat.name.lower() for cat in offer.category.all()]:
            offers.append(offer)
            if offer.discount_type == 'percentage':
                price_after_offer *= (1 - offer.discount_value / 100)
            elif offer.discount_type == 'fixed_amount':
                price_after_offer = max(0, price_after_offer - offer.discount_value)
    
    sizes = Size.objects.all().order_by('size')
    
    size_stock = {}
    for size in sizes:
        product_stock = ProductSizeStock.objects.filter(product=product, size=size).first()
        size_stock[size] = product_stock.stock if product_stock else 0
    print(size_stock)
    
    return render(request, 'product_detail.html', {
        'product': product,
        'price_after_offer': price_after_offer,
        'offers': offers,
        'sizes': sizes,
        'size_stock': size_stock
    })   
    
def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            # Salvare fișier JSON
            messages_dir = os.path.join(os.path.dirname(__file__), 'mesaje')
            os.makedirs(messages_dir, exist_ok=True)
            
            timestamp = int(time.time())
            file_name = f"mesaj_{timestamp}.json"
            file_path = os.path.join(messages_dir, file_name)

            with open(file_path, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, ensure_ascii=False, indent=4) #data este obiectul python cu care lucram, ensure_ascii salveaza caracterele cu diaccritice asa cum sunt scrise, indent specifica nivelul de indentare

            first_name=form.cleaned_data.get("first_name")
            return HttpResponse(f"Thank you, {first_name}! Your message has been sent successfully!")
    else:
        form = ContactForm()

    return render(request, "contact.html", {"form": form})



def create_product(request):
    if not request.user.has_perm('app.add_product'):
        return render(request,'403.html',{
            'username':request.user.username if request.user.is_authenticated else 'Anonymous',
            'title':'Error Adding Product',
            'message':'You do not have permission to add shoes'
            },status=403)
    
    
    if request.method == 'POST':  #se verifica daca datele au fost trimise printr-o cerere POST
        form = ProductForm2(request.POST, request.FILES) #request.POST retine datele trimise in formular iar request.FILES contine fisierele incarcate
        if form.is_valid():
            product = form.save(commit=False) #se preiua mai intai datele din campurile aditionale pentru a fi procesate
            product.name = product.name.capitalize()   
                
            limited_edition=form.cleaned_data.get('limited_edition')
            if limited_edition:
                product.limited_edition=True
            
            product.save()
            form.save_m2m() #Salvez relatiile many-to-many
            
            # Salvarea stocurilor
            for size in Size.objects.all():
                stock_field = f'stock_size_{size.id}'
                stock_value = form.cleaned_data.get(stock_field)
                if stock_value is not None :
                    ProductSizeStock.objects.create(
                        product=product,
                        size=size,
                        stock=stock_value
                    )
            
            return redirect('product_list')
    else:
        form = ProductForm2()

    return render(request, 'product_form.html', {'form': form})

    
def create_user(request):
    if request.method=='POST':
        form=CustomUserForm(request.POST,request.FILES) #request.FILES este pentru incarcat de poze 
        if form.is_valid():
            user=form.save(commit=False) #creeaza obiectul fara a-l salva in baza de date pentru a-l putea modifica
            username=user.username.lower()
            
            if username=='admin':
                mail_admins(
                    subject = "Attempt to Register as 'admin'",
                    message = f"Someone tried to register with username: {username}\nEmail: {form.cleaned_data.get('email')}",
                    html_message = f"<h1 style='color:red;'>Security Alert</h1><p>Attempt to register with username: <b>{username}</b></p>"  
                )
                return redirect('create_user')
            messages.error(request, "Registration with 'admin' username is not allowed.")
            logger.critical("Someone tried to register with 'admin' username")
            
            user.set_password(form.cleaned_data.get('password')) #modific obiectul
            user.code=get_random_string(20)
            user.save() #salvez obiectul in baza de date
            
            
            context={
                'username':user.username,
                'first_name':user.first_name,
                'last_name':user.last_name,
                'code':user.code,
                'url':'http://127.0.0.1:8000/app'
            }
            
            html_content=render_to_string('confirmation_email.html',context)
            
            email=EmailMessage(
                subject='Email Confirmation',
                body=html_content,
                from_email='balasoiu.bogdan@gmail.com',
                to=[user.email],
            )
            email.content_subtype='html' #emailul va fi interpretat ca html

            try:
                email.send(fail_silently=False) #Trimite e-mailul.Parametrul fail_silently indică dacă erorile ar trebui să fie ignorate (True) sau afișate (False).
                messages.success(
                    request, 'Your account has been successfully created! Please check your email to confirm it.')
            except Exception as e:
                logger.warning(f"An error occurred while sending the confirmation email: {e}")
                messages.warning(request,f"An error occurred while sending the confirmation email: {e}")
            return redirect('login')
    else:
        form=CustomUserForm()
    return render(request,'create_user.html',{'form':form})
                    

#obtin ip-ul clientului
def get_user_ip(request):
    ip_address=request.META.get('HTTP_X_FORWARDED_FOR') #request.META este un dicționar care conține toate anteturile HTTP și informațiile legate de cererea curentă. HTTP_X_FORWARDED_FOR este un antet HTTP utilizat de serverele proxy sau load balancers pentru a indica adresa IP reală a clientului. Dacă aplicația ta se află în spatele unui proxy, acest antet va conține IP-ul utilizatorului final.
    if ip_address:
        ip_address=ip_address.split(',')[0] #extrag primul ip
    else:
        ip_address=request.META.get('REMOTE_ADDR') #Dacă aplicația nu se află în spatele unui proxy, adresa IP a utilizatorului este direct stocată în REMOTE_ADDR. REMOTE_ADDR este antetul standard care conține IP-ul clientului în cererile directe către server.
    return ip_address

#dictionarul care memoreaza logarile esuate
failed_logins={}

def custom_login(request):
    if request.method=='POST':
        form=CustomAuthentificationForm(data=request.POST,request=request)
        if form.is_valid():
            user=form.get_user()
            
            #verific daca emailul a fost confirmat
            if not user.email_confirmed:
                messages.error(request, "Please confirm your email to log in.")
                logger.warning(f"Unconfirmed email login attempt by {user.username}.")
                return redirect('login')
            
            if user.is_blocked:
                messages.error(request,"Unfortunately you were blocked by one of our admins. You can not login:( ")
                return redirect('login')
            
            logger.debug(f"The user is {user.username}")
            login(request,user)
            if not form.cleaned_data.get('stay_logged'):
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(24*60*60)
            messages.success(request,"Connected Successfully")
            return redirect('profile')
        else:
            #trimit mail catre administratori daca cineva are 3 logari esuate in mai putin de 2 minute
            ip=get_user_ip(request)
            if not ip:
                logger.warning('IP does not exist!')
                messages.warning(request,'IP does not exist!')
            username=request.POST.get('username','Unknown')
            logger.debug(f"The user is {username}")
            login_failed_time=now()
            
            if ip not in failed_logins:
                failed_logins[ip]=[]
            failed_logins[ip].append(login_failed_time)
            
            failed_logins[ip] = [attempt for attempt in failed_logins[ip] if (login_failed_time - attempt).total_seconds() <= 120]
            logger.debug(f"The user {username} tried to login in the last 2 minutes at: {failed_logins[ip]}")
            
            if len(failed_logins[ip])>=3:
                try:
                    mail_admins(
                        subject='Suspicious login',
                        message=f"Username: {username}\n IP: {ip}",
                        html_message=f"<h1 style='color:red;'>Suspicious login</h1><p>Username: {username}</p><p>IP: {ip}</p>",
                        fail_silently=False
                    )
                    logger.critical(f"{username} has a suspicios login")
                except Exception as e:
                    mail_admins(
                        subject='Error Sending Login Alert',
                        message=f"An error occurred while sending a login alert:\n{e}",
                        html_message=(
                            "<h1 style='background-color:red;'>Error Sending Login Alert</h1>"
                            f"<p style='background-color:red;'>Details: {e}</p>"
                        ),
                        fail_silently=False
                    )
            messages.error(request, "Invalid credentials. Please try again.")
            logger.error(f"Invalid credentials for {username}")       
    else:
        form=CustomAuthentificationForm()
    
    return render(request,'login.html',{'form':form})


def custom_logout(request):
    user=request.user
    logout(request)
    messages.info(request,f"{user.username} has been logged out")
    
    try:
        permission = Permission.objects.get(codename='can_view_offer')
        
        # Verifică dacă permisiunea există în permisiunile utilizatorului
        if permission in user.user_permissions.all():
            user.user_permissions.remove(permission)
            logger.info(f'Permission "can_view_offer" has been removed for username "{user.username}"')
            messages.debug(request,f'Permission "can_view_offer" has been removed for username "{user.username}"')
        else:
            logger.info(f"User {user.username} did not have 'can_view_offer' permission")
            messages.debug(request,f"User {user.username} did not have 'can_view_offer' permission")
        
    except Permission.DoesNotExist:
        logger.error('Permission "can_view_offer" is not found')
    
    return redirect("product_list")


@login_required #doar utilizatorii logati pot accesa pagina
def profile(request):
    user=request.user
    return render (request,'profile.html',{'user':user})


@login_required
def change_password(request):
    if request.method=='POST':
        form=PasswordChangeForm(user=request.user,data=request.POST) #parametrul1 indica faptul ca formularul este pentru utilizatori autentificati, parametrul2 include datele trimise de utilizator in formular
        if form.is_valid():
            form.save()
            update_session_auth_hash(request,request.user) #modifica hash-ul de autentificare din sesiunea utilizatorului astefl incat acesta sa nu fie deconectat cand schimba parola
            messages.success(request,'The password has been successfully reseted')
            return redirect('profile')
        else:
            messages.error(request, 'The password could not be reset. Please try again.')
    else:
        form=PasswordChangeForm(user=request.user)
    
    return render(request,'change_password.html',{'form':form})


def email_confirmation(request,code):
    try:
        user=CustomUser.objects.get(code=code)
        if user.email_confirmed==False:
            user.email_confirmed=True
            user.save()
            messages.success(request,'Email confirmed successfully!')
            logger.info(f"Email confirmed for user {user.username}.")
        else:
            messages.info(request,'Email is already confirmed!')
            logger.info(f"Email for user {user.username} is already confirmed.")
    except CustomUser.DoesNotExist:
        messages.error(request,'Invalide code!')
        logger.error(f"Invalid confirmation code: {code}")
    return redirect('login')
            
            
           
def create_promotion(request):
    if request.method == 'POST':
        form = PromotionsForm(request.POST)
        if form.is_valid():
            # Creez instanța fără a salva în baza de date
            promotion = form.save(commit=False)
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            promotion.save()  # Salvez obiectul în baza de date
            form.save_m2m()  # Salvez categoriile selectate din relația many-to-many
            
            k = 2  # Numărul minim de vizualizări
            views = Views.objects.values('user', 'product__category').annotate(view_count=Count('id')) #cu annotate adaug un camp suplimentar numit view_count care numara numarul de vizualizari pentru fiecare user, filtrate pe categorie, se returneaza o lista de dictionare
            user_emails = {}

            # Filtrarea utilizatorilor cu minim K vizualizări pentru fiecare categorie
            categories = form.cleaned_data.get('category')
            for category in categories:
                eligible_users = views.filter(product__category=category, view_count__gte=k) #verififc daca utilizatorii au cel putin k vizualizari
                if category not in user_emails:
                    user_emails[category] = []

                for user_data in eligible_users:
                    user_id = user_data['user']
                    user = CustomUser.objects.get(id=user_id)
                    if user.email:
                        user_emails[category].append(user.email)
            
            # Construiesc lista de emailuri
            emails = []
            for category, emails_list in user_emails.items():
                message_email = render_to_string(f"email_promotion_{category}.html", {
                    'subject': subject,
                    'message': message,
                    'end_date': promotion.end_date
                })
                plain_message = strip_tags(message_email) #transforma mesajul HTML in text simplu, altfel functia send_mass_mail va trimite in email codul html
                emails.append((subject, plain_message, 'balasoiu.bogdan@gmail.com', emails_list))
            
            # Trimit emailurile în masă
            send_mass_mail(emails, fail_silently=False)
            logger.info(f"The email is sending to:{emails_list}")
            return redirect('product_list')
        else:
            return render(request, 'promotions.html', {'form': form})
    else:
        form = PromotionsForm()

    return render(request, 'promotions.html', {'form': form})



def view_403(request):
    if request.user.is_authenticated:
        username=request.user.username
    else:
        username='Stranger'
        
    if not request.user.has_perm('app.views'):
        return render(request,'403.html',{'username':username,
                                                                'title':'Restricted Access',
                                                                'message':'You do not have permission to access this page. Please contact the administrator.'
                                                                },status=403)
    return render(request, '403.html', {
        'username': username,
        'title': 'Access Granted',
        'message': 'You are not restricted, but this is a 403 page demo.',
    })
    
    
@login_required
def grant_offer_permission(request):
    user=request.user
    permission=Permission.objects.get(codename='can_view_offer')
    
    user.user_permissions.add(permission)
    
    return JsonResponse({'status':'succes'})


def offer_page(request):
    if request.user.has_perm('auth.can_view_offer'):
        return HttpResponse('This is an offer page')
    else:
        return render(request,'403.html',{
            'title':'Offer Error',
            'message':'You are not allowed to view the offer',
            'username':request.user.username
        })

def all_offers(request):
    active_offers = Offer.objects.filter(
        start_date__lte=timezone.now().date(),
        end_date__gte=timezone.now().date()
        ).prefetch_related('product')
    print(active_offers)
    
    return render(request,"all_offers.html",{'active_offers':active_offers})
    

def offer_detail(request, id):
    offer = get_object_or_404(Offer, id=id)
    categories=offer.category.all()
    print(categories)
    return render(request, 'offer_detail.html', {'offer': offer,'categories':categories})


 
def virtual_cart(request):
    return render(request,'virtual_cart.html')  


def order_sent(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        cart = data.get('cart', [])
        print(cart)
        
        user = request.user
        order = Order.objects.create(user=user, order_date=now().date())
        print('object created in Order')
        
        for item in cart:
            product_id = item.get('id')
            quantity = item.get('quantity')
            
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return JsonResponse({'error': f'Product with ID {product_id} does not exist.'}, status=400)
             
            OrderProduct.objects.create(
                order=order,
                product=product,
                quantity=quantity
            )
            print('object created in OrderProduct')
            
        # Redirecționează utilizatorul către pagina de confirmare a comenzii, incluzând order_id în URL
        return JsonResponse({'message': 'Order successfully placed.', 'order_id': order.id}, status=201)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

    
    
def confirmation_order_sent(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    send_order_pdf(order) 
    return render(request, "confirmation_order_sent.html", {"order": order})

    

def pdf_file():
    p=canvas.Canvas("fis.pdf")
    p.drawString(10,100,"Test")
    p.showPage()
    p.save()
    
def send_order_pdf(order):
    # Generate PDF
    pdf_path = generate_invoice(order)
    
    # Send email
    email = EmailMessage(
        subject=f"Invoice for Order #{order.id}",
        body="Thank you for your order! The invoice is attached to this email.",
        to=[order.user.email],
    )
    email.attach_file(pdf_path)
    email.send()


def generate_invoice(order):
    # File name
    timestamp = int(time.time())
    filename = f"factura-{timestamp}.pdf"
    
    # Base directory
    base_directory = "temporar-facturi"
    
    # Ensure the base directory exists
    if not os.path.exists(base_directory):
        os.makedirs(base_directory)
    
    # User-specific subdirectory
    user_directory = os.path.join(base_directory, f"{order.user.first_name}_{order.user.last_name}")
    
    # Create user-specific directory if it doesn't exist
    if not os.path.exists(user_directory):
        os.makedirs(user_directory)
    
    # Full file path for the PDF
    file_path = os.path.join(user_directory, filename)
    
    # Create PDF
    pdf = canvas.Canvas(file_path, pagesize=letter)
    pdf.setFont("Helvetica", 12)
    
    # Header
    pdf.drawString(50, 750, f"Invoice No. {order.id}")
    pdf.drawString(50, 730, f"Order Date: {order.order_date.strftime('%d-%m-%Y')}")
    pdf.drawString(50, 710, f"Customer: {order.user.first_name} {order.user.last_name}")
    pdf.drawString(50, 690, f"Customer Email: {order.user.email}")
    pdf.drawString(50, 670, "Admin Contact: balasoiu.bogdan@gmail.com")  # Replace with actual admin email
    
    # Product table
    y = 640
    total_quantity = 0
    total_price = Decimal(0.0)  # Ensure total_price is of type Decimal
    
    pdf.drawString(50, y, "Ordered Products:")
    y -= 20
    pdf.drawString(50, y, "ID | Product Name | Product Link | Quantity | Total Price")
    y -= 10
    pdf.line(50, y, 550, y)
    y -= 20
    
    for item in order.orderproduct_set.all():
        product = item.product
        product_total = product.price * item.quantity
        product_link=f"http://127.0.0.1:8000/{product.get_absolute_url}"
        pdf.drawString(50, y, f"{product.id} | {product.name} | {product_link} | {item.quantity} | {product_total:.2f}")
        y -= 20
        total_quantity += item.quantity
        total_price += Decimal(product_total)  # Convert product_total to Decimal
    
    # Totals
    pdf.drawString(50, y, f"Total Products: {total_quantity}")
    y -= 20
    pdf.drawString(50, y, f"Final Price: {total_price:.2f} RON")
    
    pdf.showPage()
    pdf.save()
    
    return file_path