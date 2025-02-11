from django import forms
from .models import Review,Product, Category, Brands, Supplier, Size,Offer,CustomUser,CategoryModel
from datetime import date
import re
from django.utils import timezone
from django.contrib.auth.forms import AuthenticationForm

  
def common_validation(value,field_name="Field"):
        
        if not re.match(r'^[A-Z]', value):
            raise forms.ValidationError(f"the {field_name} must start with uppercase")
        
        if not re.fullmatch(r'[A-Za-z ]+',value):
            raise forms.ValidationError(f"the {field_name} must contain only letters and spaces")

def calculate_age(birth_date):
    today = date.today()
    years = today.year - birth_date.year
    months = today.month - birth_date.month
    if months < 0:
        years -= 1
        months += 12
    return (years, months)



def message_spaces(message):
    message=message.replace('\n',' ')
    message=re.sub(r'\s+',' ',message)
    return message.strip()
    
    
    

class ReviewAdminForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = '__all__'
    
    rating = forms.IntegerField(
        widget=forms.NumberInput(attrs={'type': 'number', 'min': '1', 'max': '5'}),
        min_value=1,
        max_value=5,
    )
    
    
class ProductForm(forms.Form):
    name=forms.CharField(required=False,label='Name')
    description=forms.CharField(required=False,label="Description")
    price_min=forms.DecimalField(required=False,label='Min Price')
    price_max=forms.DecimalField(required=False,label='Max price')
    category=forms.ChoiceField(choices=Product._meta.get_field('category').choices,required=False,label='Category')
    brand=forms.ChoiceField(choices=Product._meta.get_field('brand').choices,required=False, label='Brand')
    supplier=forms.ModelChoiceField(queryset=Supplier.objects.all(),required=False,label='Supplier')
    size=forms.ModelChoiceField(queryset=Size.objects.all().order_by('size'),required=False,label='Size')
    
   
class ContactForm(forms.Form):
    last_name=forms.CharField(max_length=10,required=True,label='Last Name',widget=forms.TextInput(attrs={'placeholder':'last name'}))
    first_name=forms.CharField(label='First Name',widget=forms.TextInput(attrs={'placeholder':'first name'}))
    birth_date=forms.DateField(required=True,label='Birthday', widget=forms.DateInput(attrs={'type': 'date'}))
    email=forms.EmailField(required=True,label='E-mail', widget=forms.EmailInput(attrs={'placeholder': 'bogdan@gmail.com'}))
    email_confirmation=forms.EmailField(required=True,label='E-mail Confirmation', widget=forms.EmailInput(attrs={'placeholder': 'confirm your e-mail'}))
    
    message_choices=[
        ('complaint','Complaint'),
        ('question','Question'),
        ('review','Review'),
        ('request', 'Request'),
        ('appointment','Appointment')
    ]
    
    message_type=forms.ChoiceField(choices=message_choices,required=True,label="Message Type")
    subject=forms.CharField(required=True,label='Subject',widget=forms.TextInput(attrs={'placeholder':'write...'}))
    min_waiting_days=forms.IntegerField(required=True,label="Minimum waiting days",min_value=1, widget=forms.NumberInput(attrs={'placeholder': '1'}))
    message = forms.CharField(required=True,label='Message (please sign yourself at the end)',widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Write your message'}))
    
    
    def clean_last_name(self):
        last_name=self.cleaned_data.get('last_name')
        common_validation(last_name,'last name')
        return last_name
    
    def clean_first_name(self):
        first_name=self.cleaned_data.get('first_name')
        if first_name:
            common_validation(first_name,'first name')            
        return first_name
    
    def clean_subject(self):
        subject=self.cleaned_data.get('subject')
        common_validation(subject,'subject')
        return subject
    
    
    def clean(self):
        cleaned_data = super().clean() #folosim super() pentru a apela metoda clean din clasa parinte si o extindem

        email = cleaned_data.get("email")
        email_confirmation = cleaned_data.get('email_confirmation')
        if email and email_confirmation and email != email_confirmation:
            raise forms.ValidationError("Email and confirmation email do not match.")
        cleaned_data.pop("email_confirmation",None)
        
        
        birth_date = cleaned_data.get('birth_date')
        if birth_date:
            years,month=calculate_age(birth_date)
            if years<18:
                raise forms.ValidationError("you must be at least 18")
            
            cleaned_data["age"]=f"{years} years and {month} months"
            cleaned_data.pop("birth_date",None)

        message = cleaned_data.get("message")
        last_name = cleaned_data.get('last_name')
        first_name = cleaned_data.get('first_name')

        if message:
            words = re.findall(r'\w+', message)
            if len(words) < 5 or len(words) > 100:
                raise forms.ValidationError("The message must contain between 5 and 100 words, excluding links.")

            if any(word.startswith(("http://", "https://")) for word in words):
                raise forms.ValidationError("The message must not contain links.")
            
            if not ((words[-1] == last_name and words[-2] == first_name) or 
                    (words[-2] == last_name and words[-1] == first_name)):
                raise forms.ValidationError("You did not sign yourself at the end of the message.")

            cleaned_data['message']=message_spaces(message)

        return cleaned_data
    
    
class ProductForm2(forms.ModelForm):
    discount_offer = forms.ModelChoiceField(
        required=False,
        label='Discount',
        queryset=Offer.objects.all(),
        help_text="Select an active discount offer for this product."
    )
    limited_edition = forms.BooleanField(label='Limited Edition', required=False)

    class Meta:
        model = Product
        fields = ['name', 'description', 'price','image', 'supplier']
        
        
    def __init__(self, *args, **kwargs): #__ini__ - constructorul; *args și **kwargs: Acestea sunt parametri folosiți pentru a prelua argumentele poziționale și pe cele bazate pe cheie transmise la inițializarea formularului. 
        super().__init__(*args, **kwargs) #Argumentele sunt transmise metodei __init__ a clasei de bază (prin super().__init__(*args, **kwargs)).
        # Adaug câmpuri dinamice pentru fiecare mărime
        for size in Size.objects.all():
            self.fields[f'stock_size_{size.id}'] = forms.IntegerField(  #self.fields: Este un dicționar în care cheile sunt numele câmpurilor, iar valorile sunt obiecte de tip câmp (forms.Field). Adăugarea unui câmp în acest dicționar înseamnă că acel câmp va apărea în formular.
                required=True,
                min_value=0,
                label=f'Stock for size {size.size}',
                initial=0
            )

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("The name must be completed.")
        if not re.match(r'^[A-Z]', name):
            raise forms.ValidationError("The name must start with an uppercase letter.")
        words = re.findall(r'\w+', name)
        if len(words) < 2:
            raise forms.ValidationError("The name must contain at least two words.")
        return name

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description:
            raise forms.ValidationError("The description is not completed.")
        words = re.findall(r'\w+', description)
        if len(words) < 15:
            raise forms.ValidationError("The description must contain at least 15 words.")
        return description

    

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if not price:
            raise forms.ValidationError("The price must be completed.")
        if price <= 0:
            raise forms.ValidationError("The price must be a positive value.")
        return price

    def clean_discount_offer(self):
        discount_offer = self.cleaned_data.get('discount_offer')
        if discount_offer:
            today = timezone.now().date()
            if not (discount_offer.start_date <= today <= discount_offer.end_date):
                raise forms.ValidationError(
                    f"Offer '{discount_offer.name}' is not active. It cannot be applied!"
                )
        return discount_offer

    def clean_limited_edition(self):
        limited_edition = self.cleaned_data.get('limited_edition')
        price = self.cleaned_data.get('price')
        if limited_edition and (price is None or price < 50):
            raise forms.ValidationError("Limited Edition products must have a price greater than 50.")
        return limited_edition

    def clean(self):
        cleaned_data = super().clean()
        if self.errors:
            return cleaned_data

        name = cleaned_data.get('name')
        description = cleaned_data.get('description')

        if name and description and name not in description:
            raise forms.ValidationError("The product name must be mentioned in the description.")

        return cleaned_data
    
    
class CustomUserForm(forms.ModelForm):
    confirm_password=forms.CharField(required=True,label='Confirm Password',widget=forms.PasswordInput)
    
    class Meta:
        model=CustomUser
        fields=[
            'first_name',
            'last_name',
            'username',
            'email',
            'password',
            'phone_number',
            'birth_date',
            'profile_picture',
            'country',
            'city',
            'address',
            'postal_code'
        ]
        
        widgets={
            'password':forms.PasswordInput(),
            'birth_date':forms.DateInput(attrs={'type':'date'}),
            'address':forms.Textarea(attrs={'rows':3,'cols':40}),
            'phone_number':forms.TextInput(attrs={'placeholder':'(+40)07xx xxx xxx'}),
            'email':forms.TextInput(attrs={'placeholder':'exemple@gmail.com'}),
        }
        
    field_order=[
    'first_name',
    'last_name',
    'username',
    'email',
    'password',
    'confirm_password', 
    'phone_number',
    'birth_date',
    'profile_picture',
    'country',
    'city',
    'address',
    'postal_code'
    ]
    
    def clean_first_name(self):
        first_name=self.cleaned_data.get('first_name')
        if not first_name:
            raise forms.ValidationError('First name is required')
        return first_name
        
    def clean_last_name(self):
        last_name=self.cleaned_data.get('last_name')
        if not last_name:
            raise forms.ValidationError('Last name is required')
        return last_name

    def clean_phone_number(self):
        phone_number=self.cleaned_data.get('phone_number')
        valid_phone_number=re.fullmatch(r'(\+40)?[0-9]{9,10}',phone_number)
        if not valid_phone_number:
            raise forms.ValidationError("Phone number is not valid")
        return phone_number
    
    def clean_country(self):
        country = self.cleaned_data.get('country')
        if not re.match(r'^[a-zA-Z\s\-]+$', country):
            raise forms.ValidationError('Country name can only contain letters, spaces, and hyphens.')
        return country

    def clean_city(self):
        city = self.cleaned_data.get('city')
        if not re.match(r'^[a-zA-Z\s\-]+$', city):
            raise forms.ValidationError('City name can only contain letters, spaces, and hyphens.')
        return city
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already registered.')
        if "gmail.com" not in email:
            raise forms.ValidationError("Please use a 'gmail.com' email address")
        
        return email

    def clean(self):
        cleaned_data=super().clean()
        confirm_password=cleaned_data.get('confirm_password')
        password=cleaned_data.get('password')
        
        if password:
            has_digit=bool(re.search(r'\d+',password))
            has_special_charecter=bool(re.search(r'[^a-zA-Z0-9]',password))
            has_uppercase=bool(re.search(r'[A-Z]+',password))
        
        if len(password)<8 or not has_digit or not has_special_charecter or not has_uppercase:
            raise forms.ValidationError('The password must have at least 8 characters, including at least 1 digit, 1 special character and 1 uppercase')
        
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Password confirmation and password do not match')
        
        return cleaned_data
    
    
    
class CustomAuthentificationForm(AuthenticationForm):
    stay_logged=forms.BooleanField(required=False,initial=False,label='Stay logged in')
    
    def clean(self):
        cleaned_data=super().clean()
        stay_logged=self.cleaned_data.get('stay_logged')
        return cleaned_data
    
    
class PromotionsForm(forms.ModelForm):
    subject=forms.CharField(required=True,label='Subject')
    message=forms.CharField(required=True,label='Message')
    
    class Meta:
        model=Offer
        fields=['name','discount_type','discount_value','start_date','end_date','category']
        widgets={
            'start_date':forms.DateInput(attrs={'type':'date'}),
            'end_date':forms.DateInput(attrs={'type':'date'})
        }