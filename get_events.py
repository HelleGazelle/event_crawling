from bs4 import BeautifulSoup
import re
import requests
import csv

field_name = ['id', 'eventname', 'location', 'organization', 'date', 'event_details']


crawled_event_ids = []
with open(file="out.csv", mode="r") as db_file:
    reader = csv.DictReader(f=db_file)
    for row in reader:
        crawled_event_ids.append(row["id"])

counter = 0

def get_event_detail(id: str):
    html_content = requests.get(f"https://partyfax.de/termin/?id={id}").content

    soup = BeautifulSoup(html_content, 'html.parser')

    details_object = {}

    main_section = soup.find_all('div', class_="entry-content")[0]
    heading = main_section.find_all('h3')[0].find_next_sibling(string=True).strip()
    date_pattern = r"\b(\d{2}\.\d{2}\.\d{4})\b"
    match = re.search(date_pattern, heading)
    details_object['date'] = match.group(1)
    
    event_details = ""
    hr_tag = main_section.find('hr')
    if hr_tag:
        for sibling in hr_tag.find_next_siblings(string=True):
            if sibling.name == 'hr':
                break
            if sibling.string:
                event_details = event_details + " " + sibling.string.strip()
                event_details = event_details.replace("\t", "").replace("\n", "")

    details_object['event_details'] = event_details

    return details_object

# with open('static/archive.html', mode='r') as htmlfile:
#     html_content = htmlfile.read()

html_content = requests.get(f"https://partyfax.de/nach-datum/").content

soup = BeautifulSoup(html_content, 'html.parser')

event_objects = []

# Find all "a" elements
pattern = re.compile( r"/termin/\?id=[^&/]+")
a_elements = soup.find_all('a', href=pattern)

with open(file="out.csv", mode="a") as out_file:
    writer = csv.DictWriter(f=out_file, fieldnames=field_name)
    writer.writeheader()

    for a in a_elements:
        event_object = {}

        # Extract id
        href_content = a.get('href')
        match = re.search(r'=(\w+)$', href_content)
        event_id = match.group(1)
        event_object['id'] = event_id

        if event_id in crawled_event_ids:
            continue
        
        # Extract eventname
        eventname_label = a.find('label', class_='eventname')
        if eventname_label:
            event_object['eventname'] = eventname_label.get_text(strip=True).replace("\t", "").replace("\n", " ")
        
        # Extract location
        table_rows = a.select('div > table > tr > td', attrs={'class': 'eventcol'})
        if len(table_rows) == 4:
            del table_rows[1]
        
        if len(table_rows) > 0:
            location_td = table_rows[1]
            event_object['location'] = location_td.get_text(strip=True)
        
        # Extract organization
        
        if len(table_rows) > 1:
            organization_td = table_rows[2]
            event_object['organization'] = organization_td.get_text(strip=True)
        
        
        details = get_event_detail(event_id)
        event_object.update(details)
        
        counter = counter + 1
        if counter % 10 == 0:
            print(counter)
        # if counter == 50:
        #     break
        writer.writerow(event_object)



    
    
