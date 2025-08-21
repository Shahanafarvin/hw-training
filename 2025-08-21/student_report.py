"""
Task 2.A: Student Marks and Report Generator

Objective - Build a student record system that uses multiple data types and logic.
"""

# creating  variable for student details
name = "Shahana"
age = 22
marks = [78.5, 64.0, 85.5]

# creating a dictionary to store student details
student = {
    "name": name,
    "age": age,
    "marks": marks
}

#printing the datatypes of each value in the dictionary
print("\nData Types of Each Value:")
for key, value in student.items():
    print(f"{key}: {type(value)}")

#calculating total and average marks
total_marks = sum(marks)
average_marks = total_marks / len(marks)
print("\nTotal Marks:", total_marks)
print("Average Marks:", average_marks)

# determining if the student has passed or failed
if average_marks >= 40:
    is_passed = True
else:
    is_passed = False

# printing individual marks
print("\nIndividual Marks:")
for i in range(len(marks)):
    print(f"Subject {i+1}: {marks[i]}")

# converting marks to a set 
marks_set = set(marks)
print("\nMarks as Set:", marks_set)

#storing subjects in a tuple
subjects = ("Maths", "Science", "English")
print("\nSubjects:", subjects)

# adding a variable for remarks
remarks = None
print("\nRemarks:", remarks, "Type:", type(remarks))

# checking the type of is_passed variable
print("\nType of is_passed :", type(is_passed))

#ptinting the student report
print("\n---- Student Report ----")
print(f"Name: {name}")
print(f"Age: {age}")
print(f"Subjects: {subjects}")
print(f"Marks: {marks}")
print(f"Total Marks: {total_marks}")
print(f"Average Marks: {average_marks:.2f}")
print(f"Result: {'Passed' if is_passed else 'Failed'}")
