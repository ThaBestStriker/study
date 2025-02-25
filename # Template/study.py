# version 1.04
# 14 May 2019
# C. Holland
# 741258+scripts@pm.me
# CHANGELOG
# 4/3/19 - fitb answers and the answers from the text file are stripped of trailing whitespace when matching
# 4/3/19 - when processing imported lines from the text file into questions, lines with only whitespace are ignored
# 4/12/19 - added time elapsed and answer accuracy in the heading
# 4/20/19 - added support for case sensitivity using an additional column in the xlsx
# 4/20/19 - added support for multiple correct answer variations in fitb questions
# 4/21/19 - added support for any order answers for fitb questions
# 4/21/19 - double quotes are removed from all lines when parsing the tab-sep file to account for excel nonsense
# 4/21/19 - added support for 'sorting' question. Example: place these process steps in order.
# 4/21/19 - added a session results display after all questions have been answered.
# 5/14/19 - added OS detection and manual console clear command entry as a fallback
# 6/20/19 - added support for newline escape sequence in question text
# 6/20/19 - script will detect questions sets automatically
# 6/24/19 - added 0 (zero) option to set selection to select all sets


import random, os, textwrap, datetime, re, sys

choice_selectors = ['a','s','d','f']  # up to four selectors to use for the multiple choice answer selection, use single or double quotes around each selector
consecutive_correct_count = 1  # modify to change the required number of consecutive correct answers to move a question into the learned pool


class QuestionHandler():
    def __init__(self, question_set, user_active_sets):
        self.question_bank = [q for q in question_set if q.question_set in user_active_sets]
        self.active_question_pool = []
        self.learned_question_pool = []
        self.answer_bank = self.make_answer_bank()
        self.user_active_sets = user_active_sets


        # generate multiple choice answers for each question
        for question_index in range(len(self.question_bank)):
            if self.question_bank[question_index].category not in ('fitb','sort'):
                if type(self.question_bank[question_index].incorrect_answers) == list:
                    potential_answers = self.question_bank[question_index].incorrect_answers
                    answer_count = 1
                else:
                    potential_answers = self.answer_bank[self.question_bank[question_index].category][:]
                    answer_count = 0
                    #print "{} -- {}".format(self.question_bank[question_index].category,self.answer_bank[self.question_bank[question_index].category])
                all_selectors = choice_selectors
                for i in potential_answers:
                    if i:
                        answer_count+=1
                #print "question index: {} -- answer_count {} -- potential_answers: {}".format(question_index, answer_count, potential_answers)
                selectors = all_selectors[0:answer_count]
                #print "question index: {} -- selectors: {}".format(question_index, selectors)
                correct_selector = selectors[random.randint(0,len(selectors)-1)]
                #print 'question index: {} -- correct selector: {} -- correct answer: {}'.format(question_index, correct_selector, self.question_bank[question_index].answer)
                # assign correct answer
                self.question_bank[question_index].multiple_choice_answers[correct_selector] = self.question_bank[question_index].answer
                selectors.remove(correct_selector)

                while len(potential_answers) > 0 and len(selectors) > 0:
                    potential_answer = potential_answers[random.randint(0,len(potential_answers)-1)]
					# check to see if the question answer is the same as one of the 'incorrect answers'
                    if potential_answer != self.question_bank[question_index].answer and potential_answer not in list(self.question_bank[question_index].multiple_choice_answers.values()):
                        selector = selectors[random.randint(0,len(selectors)-1)]
                        self.question_bank[question_index].multiple_choice_answers[selector] = potential_answer
                        selectors.remove(selector)
                    potential_answers.remove(potential_answer)
                #print self.question_bank[question_index].multiple_choice_answers

        # generate initial active question pool
        for question_count in range(min(20,len(self.question_bank))):
            random_index = random.randint(0,len(self.question_bank)-1)
            selected_question = self.question_bank[random_index]
            self.active_question_pool.append(selected_question)
            self.question_bank.remove(self.question_bank[random_index])


    def make_answer_bank(self):
        answer_bank = {}
        for question in self.question_bank:
            #print "question: {}\ncategory: {}".format(question.question_text,question.category)
            if question.incorrect_answers == 'null' and question.category not in ('fitb', 'sort'):  # question doesn't have self-specific answers and is not fill in the blank or sort
                #print "No specific answers"
                if question.category not in answer_bank:
                    #print "New Category"
                    answer_bank[question.category] = []
                clean_answer = question.answer
                clean_answer = clean_answer.strip()
                if clean_answer not in answer_bank[question.category]:
                    answer_bank[question.category].append(clean_answer)
        return answer_bank

    def get_multiple_choice_question(self):
        self.active_question_index = random.randint(0, len(self.active_question_pool) - 1)
        question_data = {}
        question_data['index'] = self.active_question_index
        question_data['question_text'] = self.active_question_pool[self.active_question_index].question_text
        if self.active_question_pool[self.active_question_index].category not in ('fitb', 'sort'):
            question_data['multiple_choice_answers'] = self.active_question_pool[self.active_question_index].multiple_choice_answers
        if self.active_question_pool[self.active_question_index].category == 'sort':
            question_data['sorted_answers'] = self.active_question_pool[self.active_question_index].sorted_answers
        question_data['category'] = self.active_question_pool[self.active_question_index].category
        question_data['consecutive_correct'] = self.active_question_pool[self.active_question_index].consecutive_correct
        question_data['question_set'] = self.active_question_pool[self.active_question_index].question_set
        return question_data

    def check_answer(self, index, user_choice):
        correct = False
        match_all = False
        if self.active_question_pool[index].category == 'fitb':
            correct = True
            user_answers = user_choice.split(',')
            user_answers = [a.strip() for a in user_answers]

            if '+' in self.active_question_pool[index].answer:
                question_answers = self.active_question_pool[index].answer.split('+')
                question_answers = [a.strip() for a in question_answers]
                match_all = True
            else:
                question_answers = self.active_question_pool[index].answer.split(',')

            if len(user_answers) == len(question_answers):
                if match_all:
                    if not self.active_question_pool[index].case_sensitive:
                        question_answers = [a.lower() for a in question_answers]
                        user_answers = [a.lower() for a in user_answers]
                    for answer in user_answers:
                        if answer in question_answers:
                            question_answers = [a for a in question_answers if a != answer]
                            correct = True
                        else:
                            correct = False
                            break
                else:
                    for answer in question_answers:
                        if not self.active_question_pool[index].case_sensitive:
                            answer = answer.lower()
                        if '|' in answer:
                            answer = answer.strip().split('|')

                        cur_answer = user_answers.pop(0).strip()
                        if not self.active_question_pool[index].case_sensitive:
                            cur_answer = cur_answer.lower()
                        if cur_answer not in answer:
                            correct = False
                            break
                        else:
                            correct = True
            else:
                correct = False
        elif self.active_question_pool[index].category == 'sort':
            answer = self.active_question_pool[index].answer.split('||')
            answer = [i.strip() for i in answer]
            if user_choice == answer:
                correct = True
            else:
                correct = False
        else:
            if user_choice.lower().strip() == self.active_question_pool[index].answer.lower().strip():
                correct = True

            else:
                pass

        if correct:
            print("\nCorrect")
            self.active_question_pool[index].consecutive_correct += 1
            if self.active_question_pool[index].consecutive_correct == consecutive_correct_count:
                self.update_active_pool()

        elif not correct:
            print("\nIncorrect")
            if self.active_question_pool[index].category == 'sort':
                print("\nCorrect Order")
                print("\n-------------")
                num = 1
                for i in answer:
                    print("{} -- {}".format(num,i))
                    num+=1
            elif len(self.active_question_pool[index].answer) > 70:
                answer_wrapped = textwrap.wrap(self.active_question_pool[index].answer, 70)
                print("\nCorrect answer: {}".format(answer_wrapped[0]))
                for line in answer_wrapped[1:]:
                    print("                {}".format(line.replace('|',' OR ').replace('+',' AND ')))
            else:
                print("\nCorrect answer: {}".format(self.active_question_pool[index].answer.replace('|',' OR ').replace('+',' AND ')))
            self.active_question_pool[index].consecutive_correct = 0
        input()
        return correct








    def update_active_pool(self):
        self.learned_question_pool.append(self.active_question_pool[self.active_question_index])
        #print "removing: index: {} {}".format(self.active_question_index, self.active_question_pool[self.active_question_index].question_text)
        self.active_question_pool.remove(self.active_question_pool[self.active_question_index])
        if len(self.question_bank) > 0:
            new_active_question = self.question_bank[random.randint(0,len(self.question_bank) - 1)]
            self.active_question_pool.append(new_active_question)
            self.question_bank.remove(new_active_question)



class Question():
    def __init__(self, raw_text_line):
        question_components = raw_text_line.split("\t")
        #print raw_text_line
        self.question_text = question_components[0]
        self.answer = question_components[1]
        self.category = question_components[2]
        self.incorrect_answers = question_components[3].strip()
        self.multiple_choice_answers = {'a':None,'s':None,'d':None,'f':None}
        if self.incorrect_answers.strip() != 'null':
            self.incorrect_answers = self.incorrect_answers.split('||')
        self.question_set = question_components[4].strip()
        self.consecutive_correct = 0
        self.fitb_answers = []
        self.sorted_answers = []
        if self.category == 'fitb':
            self.fitb_answers = self.answer.split(',')
        if self.category == 'sort':
            self.sorted_answers = self.answer.split('||')
        case_sense = question_components[5]
        if case_sense.strip().lower() == 'false':
            self.case_sensitive = False
        else:
            self.case_sensitive = True


def import_questions():
    file_list = os.listdir(os.getcwd())
    question_files = []
    for file_name in file_list:
        if re.search(r'mod_[0-9]+_questions_tab\.txt', file_name):
            question_files.append(file_name)
    if len(question_files) > 1:
        os.system(clear_console_command)
        print("Choose Mod from the following list of available mods.")
        found_mods = [int(f_name.split('_')[1]) for f_name in question_files]
        found_mods.sort()
        for mod in found_mods:
            print('Mod %s' % str(mod))
        choice = ''
        while choice not in found_mods:
            choice = int(input("Enter mod number> "))
        question_file = 'mod_%s_questions_tab.txt' % str(choice)

    elif len(question_files) == 1:
        question_file = question_files[0]

    elif len(question_files) == 0:
        os.system(clear_console_command)
        print("No question files found. Make sure a mod_[mod num]_questions_tab.txt file is present.")
        sys.exit(0)

    filename = question_file
    with open(filename) as raw_text:
        raw_text_lines = raw_text.readlines()
    return raw_text_lines


def make_questions(raw_text_lines):
    question_set = []
    for line in raw_text_lines[1:]:
        stripped_line = line.replace('"','').strip()
        if len(stripped_line) > 0:
            question_set.append(Question(stripped_line))
    return question_set


def get_sets(questions):
    sets = {}
    for question in questions:
        if question.question_set in list(sets.keys()):
            sets[question.question_set]+=1
        else:
            sets[question.question_set] = 1
    return sets


clear_console_command = ""
if os.name == 'posix':
    clear_console_command = "clear"
elif os.name == 'nt':
    clear_console_command = "cls"
else:
    print("Unable to determine OS: %s")
    clear_console_command = input("Enter the command used to clear the console: ")

text = import_questions()
question_set = make_questions(text)
sets = get_sets(question_set)
in_menu = True
while in_menu:
    selection_map = {}
    active_sets = []
    os.system(clear_console_command)
    print("="*100)
    print("|{:^98}|".format("Question Set Selection"))
    print("="*100)
    set_index = 1
    valid_indexes = []
    for i in sorted(sets.keys()):
        selection_map[str(set_index)]=i
        line = "[{}] --- {} ({} Questions)".format(set_index,i, sets[i])
        print("|{:<98}|".format(line))
        set_index+=1

    print("="*100)
    print("Select question sets for this session, enter 0 to study all sets. Use commas")
    print("to select multiple sets. e.g. 1,3,7")
    set_selection = input("> ").split(',')
    invalid_selection = False
    if set_selection[0] == '0':
        active_sets = list(selection_map.values())
        if not invalid_selection:
            in_menu = False
    else:
        for i in set_selection:
            if i not in list(selection_map.keys()):
                invalid_selection = True
                print("{} not a valid selection.".format(i))
            else:
                active_sets.append(selection_map[i])
        if not invalid_selection:
            in_menu = False
        else:
            input("Press enter to try again.")
os.system(clear_console_command)
print("Press enter to begin studying the following sets:\n")
for i in active_sets:
    print(i)
input()

q_handler = QuestionHandler(question_set,active_sets)
os.system(clear_console_command)

question_attempts = 0
correct_count = 0
start_time = datetime.datetime.now()
total_questions = len(q_handler.question_bank)+len(q_handler.active_question_pool)
while len(q_handler.active_question_pool) > 0:
    new_question = q_handler.get_multiple_choice_question()
    current_time = datetime.datetime.now()
    time_elapsed = current_time - start_time
    if correct_count == 0:
        accuracy = 0
    else:
        accuracy = (float(correct_count) / question_attempts) * 100
    time_list = str(time_elapsed).split('.')[0].split(':')
    print("Question Bank: {} | Active: {} | Learned: {} | Time Elapsed: {}h {}m {}s | Answer Accuracy: {:.2f}%".format(len(q_handler.question_bank),
                                                                                                      len(q_handler.active_question_pool),
                                                                                                      len(q_handler.learned_question_pool),
                                                                                                      time_list[0],time_list[1],time_list[2], float(accuracy)))
    print("-"*100)
    #print "index: {} [{}] ({}/3) Question: {}".format(new_question['index'], new_question['category'], new_question['consecutive_correct'], new_question['question_text'])

    if '\\n' in new_question['question_text']:
        question_text_lines = new_question['question_text'].split('\\n')
        if len(question_text_lines[0]) > 70:
            first_line_wrapped = textwrap.wrap(question_text_lines[0], 70)
            print("({}/{}) Question: {}".format(new_question['consecutive_correct'], consecutive_correct_count,
                                                first_line_wrapped[0]))
            for line in first_line_wrapped[1:]:
                print("                {}".format(line))  # 16 spaces
        else:
            print("({}/{}) Question: {}".format(new_question['consecutive_correct'], consecutive_correct_count,
                                                question_text_lines[0]))
        for line in question_text_lines[1:]:
            if len(line) > 70:
                question_text_lines = textwrap.wrap(line, 70)
                for wrapped_line in question_text_lines:
                    print("                {}".format(wrapped_line))  # 16 spaces
            else:
                print("                {}".format(line))  # 16 spaces

    elif len(new_question['question_text']) > 70:

        question_text_wrapped = textwrap.wrap(new_question['question_text'],70)
        print("({}/{}) Question: {}".format(new_question['consecutive_correct'], consecutive_correct_count, question_text_wrapped[0]))
        for line in question_text_wrapped[1:]:
            print("                {}".format(line))
    else:
        print("({}/{}) Question: {}".format(new_question['consecutive_correct'], consecutive_correct_count, new_question['question_text']))
    if new_question['category'] == 'sort':
        mixed_answers = new_question['sorted_answers']
        random.shuffle(mixed_answers)
        option_number = 1
        for i in mixed_answers:
            print("                {} - {}".format(option_number, i.strip()))
            option_number+=1
    print("\nQuestion Set: {}".format(new_question['question_set']))
    print("-"*100)

    if new_question['category'] == 'fitb':
        print("Enter your answer below.\n")
    elif new_question['category'] == 'sort':
        print("Place the options in order using the number provided. Example (1,4,3,5,2)\n")
    else:
        #keys = sorted(new_question['multiple_choice_answers'].keys()) # uncomment this and comment the line below to have selectors presented in alpha-numeric order
        keys = list(new_question['multiple_choice_answers'].keys())
        for selector in keys:
            answer = new_question['multiple_choice_answers'][selector]
            if answer:
                answer = answer.strip()
                answer = answer.replace("\\t","\t")
                if "\\n" in answer:
                    answer = answer.split("\\n")
                    print("\n{} -- {}".format(selector, answer[0]))
                    for i in answer[1:]:
                        print("     {}".format(i))
                else:
                    if len(answer) > 70:
                        line_wrapped_answer = textwrap.wrap(answer, 70)
                        print("\n{} -- {}".format(selector, line_wrapped_answer[0]))
                        for line in line_wrapped_answer[1:]:
                            print("     {}".format(line))
                    else:
                        print("\n{} -- {}".format(selector, answer))

            else:
                #print "{} -- {}".format(selector, answer)
                pass
    choice = ''
    if new_question['category'] == 'fitb':
        while not choice:
            choice = input('\n> ')
        correct = q_handler.check_answer(new_question['index'], choice)
    elif new_question['category'] == 'sort':
        while not choice:
            choice = input('\n> ')
        translated_choice = []
        user_choices = choice.split(',')
        user_choices = [i.strip() for i in user_choices]
        invalid = False
        for i in user_choices:
            try:
                int(i)
            except:
                print("Invalid option: {}".format(i))
                invalid = True
        if not invalid:
            user_choices = [int(i) for i in user_choices]
            translated_choice = [mixed_answers[i-1] for i in user_choices]
        else:
            translated_choice = ['null' for i in user_choices]
        correct = q_handler.check_answer(new_question['index'], translated_choice)
    else:
        while choice not in choice_selectors:
            choice = input("\n> ").lower()
        correct = q_handler.check_answer(new_question['index'],new_question['multiple_choice_answers'][choice])
    if correct:
        correct_count += 1
    question_attempts+=1
    if correct_count == 0:
        accuracy = 0
    else:
        accuracy = (float(correct_count) / question_attempts) * 100
    os.system(clear_console_command)
print("\nSession Results")
print("---------------")
print("Session Time: {}h {}m {}s".format(time_list[0],time_list[1],time_list[2]))
print("Question Bank Size: {}".format(total_questions))
print("Question Attempts: {}".format(question_attempts))
print("Answer Accuracy: {:.2f}%".format(float(accuracy)))
print("Sets Studied:")
for i in active_sets:
    print("             {}".format(i))

input("\n\nPress Enter to exit")



