Python Version: 3+
OS: Windows/Linux

Description
-----------
This program is a command-line testing engine which supports the following question types:

* Multiple Choice
* Fill in the Blank (single/multiple answers)
* Sorting

Testing Design
--------------
The testing engine allows the user to specify a required number of consecutive correct answers on a given question for the question to become 'learned'. Twenty questions are pulled from the selected mod/category into the 'active pool'. Once a question is answered correctly, consecutively, the number of times indicated, the question leaves the active pool and a new question takes its place. This can greatly increase learning effectiveness by drilling difficult questions in a short time period rather than randomly pulling from the entire question set.

This option is set near the top of the source code where the following line is found:
consecutive_correct_count = 1

While testing, the answered count and required consecutive count are shown next to the question as follows.
(1/3) What is 1 + 1?

This means the question has already been answered one time correctly and requires a total of three consecutive correct answers to leave the active pool.

Creating Questions
------------------
The program imports tab separated text files (as exported by Excel or other spreadsheet software) and parses the lines to build the question data structure. View the Demo Questions set to see an example of each supported question type. As this was written without much time for design or iteration, there is a lack of error checking in place. To prevent crashing, follow these basic rules. 

* Use the 'empty_questions_template.xlsx' file to begin creating questions. Each column MUST have a value.
* The following characters are reserved for answers/questions formatting and boolean operations. (|+)
* Answers are submitted comma-separated by the user and split by the program into multiple values. The commas are not available to the answer checking function. This means you can not expect the user to answer a question in which the comma is a part of the answer. Check out the demo question showing a fill-in-the-blank question with multiple answers as an example of this.
* Name the resulting question set as 'mod_#_questions_tab.txt'
* Newline \n and tab \t are supported in question text.


Bugs/Problems
-------------
If you have any problems at any time, email me at 741258+scripts@pm.me with the Python traceback and the question/set that caused the error. 