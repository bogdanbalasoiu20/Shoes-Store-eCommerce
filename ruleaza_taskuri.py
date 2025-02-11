import schedule
import time
import django
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from app import tasks

def run_scheduler():
    schedule.every(15).minutes.do(tasks.remove_unconfirmed_users) #functia remove_unconfirmed_users este apelata automat la fiecare k minute
    schedule.every().tuesday.at("18:06").do(tasks.send_newsletter)
    schedule.every(5).minutes.do(tasks.delete_products_without_image)
    schedule.every().tuesday.at("22:15").do(tasks.random_discount_code)
    print("Scheduler initialized. Running tasks...")
    while True:
        print("Running scheduled tasks...")
        schedule.run_pending() #functie care verifica daca exista taskuri programate de rulare la mom. respectiv
        time.sleep(1) #pauza de o secunda intre fiecare verificare. previne ca bucla sa ruleze continuu si sa consume excesiv resursele procesorului
        
        
if __name__ == '__main__':
    try:
        run_scheduler()
    except KeyboardInterrupt: #opresc manual rularea automata
        print("Scheduler manually stopped")
        sys.exit()
