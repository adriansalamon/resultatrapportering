#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import requests
import os
from canvas import get_courses, get_list, get_object, Student
from difflib import SequenceMatcher

content_types = {"application/pdf": "pdf", "text/plain": "txt"}

if len(sys.argv) != 3:
    print("kör så här: inlämningshämtare.py <(del av) kurs-namn> <uppgiftsnamn>")
    sys.exit(1)

courses = get_courses(sys.argv[1])


if len(courses) == 0:
    print("hittade ej angiven kurs")
    sys.exit(1)

elif len(courses) == 1:
    course = courses[0]

else:
    i = 1

    print("index  startdatum  kurskod  namn")

    for course in courses:
        print("{0: <6}".format(str(i)), end=" ")
        print(course.date_start, end="  ")
        print(course.code, end="   ")
        print(course.name)

        i += 1

    print()

    print("flera kurser hittades -- ange index för den kurs du vill hantera:")
    course_choice = input(">> ")

    print()

    try:
        course = courses[int(course_choice) - 1]

    except:
        print("ogiltigt val av kurs, avbryter")
        sys.exit(1)

assignments = course.get_assignments()
assignment = next((a for a in assignments if a.name == sys.argv[2]), None)

addresses = []

if assignment is None:
    print("hittade ej angiven uppgift")
    sys.exit(1)

try:
    fh = open("adresser.txt", "r")
    for line in fh:
        name, email = line.strip().split(",")
        addresses.append((name, email))
    fh.close()

    if len(addresses) == 0:
        print("filen adresser.txt verkar vara tom")
        sys.exit(1)

    print("sparar endast inlämningar för de i adresser.txt...")

except:
    email_addresses = []
    print("sparar alla inlämningar för " + str(course) + "...")

submissions = get_list(
    "/courses/"
    + str(course.id)
    + "/assignments/"
    + str(assignment.id)
    + "/submissions?include[]=user"
)
submissions = [
    s for s in submissions if "attachments" in s and len(s["attachments"]) > 0
]

saved_email_addresses = set()

base_folder = "inlämningar/" + course.code + "-" + assignment.name + "/"
os.makedirs(base_folder, exist_ok=True)

for submission in submissions:
    student = Student(submission["user"])

    include = False
    for name, email in addresses:
        if student.email_address == email:
            include = True
        # similarity, names might be slightly different
        if SequenceMatcher(None, student.name, name).ratio() > 0.8:
            include = True

    if not include:
        continue

    i = 1

    for attachment in submission["attachments"]:
        if attachment["content-type"] not in content_types:
            print("\thoppar över " + attachment["display_name"])
            continue

        print("\tsparar " + attachment["display_name"])
        response = requests.get(attachment["url"])

        user_name = student.email_address.split("@kth.se")[0]
        file_name = (
            user_name + "-" + str(i) + "." + content_types[attachment["content-type"]]
        )

        fh = open(base_folder + file_name, "wb")
        fh.write(response.content)
        fh.close()

        saved_email_addresses.add(student.email_address)

        i += 1

if len(addresses) > 0:
    unhandled_email_addresses = [
        x for _, x in addresses if x not in saved_email_addresses
    ]

    if len(unhandled_email_addresses) == 0:
        print(
            "samtliga giltiga inlämningar från studenter i e-postadresser.txt sparades"
        )

    else:
        print("dessa studenter i e-postadresser.txt saknade giltiga inlämningar:")
        for email_address in unhandled_email_addresses:
            print("\t" + email_address)
