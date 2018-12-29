import json
import psycopg2
import os

# globals
DB_NAME = os.environ.get('sf_db_name')
DB_USER = os.environ.get('sf_db_user')
DB_HOST = os.environ.get('sf_db_host')
DB_PASSWORD = os.environ.get('sf_db_password')

def make_connection():
	"""
	Makes a psycopg2 connection to the database and returns a psycopg2 connection object.

	:returns: Psycopg2 connection object credentialed with the global variables populated from env variables.
	:rtype: psycopg2 connection object
	"""

	return psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST)

def add_account(first_name, last_name, is_teacher, is_student, email, affiliation, username):
	"""
	Adds a new account entry to the accounts table in the database

	:param: str first_name: First name of the new account user.
	:param: str last_name: Last name of the new account user.
	:param: bool is_teacher: Boolean indicator whether a person is a teacher or not.
	:param: bool is_student: Boolean indicator whether a person is a student or not.
	:param: str email: Email of the new account user.
	:param: str affiliation: Academic affiliation of the new user.
	:param: str username: Username chosen by user
	:returns: ID of new account created
	:rtype: int
	"""

	try:
		# Create a connection
		conn = make_connection()

		# Create a cursor
		cur = conn.cursor()

		# Query
		query = """
		INSERT INTO accounts
		SET first_name = %s, last_name = %s, is_teacher = %s, is_student = %s, email = %s, affiliation = %s, username = %s, classes = %s
		RETURNING id
		"""

		# Make query commit
		values = (first_name, last_name, is_teacher, is_student, email, affiliation, username, json.dumps([]))
		cur.execute(query, values)
		conn.commit()

		# Get the account id
		account_id = cur.fetchone()[0]

		# Add the user to the responses table if they're a student
		if is_student:
			query = """
			INSERT INTO student_responses
			SET student_id = %s, raw_responses = %s, responses_scores = %s
			"""

			values = (account_id, json.dumps({}), json.dumps({}))
			cur.execute(query, values)
			conn.commit()

		# Close connection
		cur.close()
		conn.close()

		return account_id

	except psycopg2.Error as e:
		print("Error connecting to database with error: {}".format(e))

def add_class(class_creator_id, class_name, subject, topics):
	"""
	Adds a new class etnry to the classes table in the database

	:param: int class_creator_id: ID of the account that created the class
	:param: str class_name: Name of the class that is being created
	:param: str subject: Subject of the class that is being created.
	:param: list topics: List of topics that the class is being created with.
	:returns: ID of the new class created and class_code to identify class for students
	:rtype: tuple
	"""

	try: 

		# Create a connection
		conn = make_connection()

		# Create a cursor
		cur = conn.cursor()

		# Query
		query = """
		INSERT INTO classes 
		SET class_creator_id = %s, name = %s, subject = %s, topics = %s 
		RETURNING id
		"""

		# Make query commit
		values = (class_creator_id, class_name, subject, json.dumps(topics))
		cur.execute(query, values)
		conn.commit()

		# Class id
		class_id = cur.fetchone()[0]

		# Get existing class codes
		query = """
		SELECT class_code FROM classes
		"""

		# Make query commit
		cur.execute(query)
		conn.commit()

		codes = cur.fetchall()

		# autogenerate class code
		class_code = None

		while class_code is None:
			tmp = random.randint(1,999999)
			if tmp not in codes:
				class_code = tmp

		# Update class table
		query = """
		UPDATE classes
		SET class_code = %s
		WHERE id = %s
		"""

		values = (class_code, class_id)
		cur.execute(query, values)
		conn.commit()

		cur.close()
		conn.close()

		return (class_id, class_code)

def join_class(user_id, class_code):
	"""
	Connects a user with the class that they wish to register for

	:param: int user_id: User id of new user to be added
	:param: int class_code: Code for the class the user wishes to join
	"""

	# Create a connection
	conn = make_connection()

	# Create a cursor
	cur = conn.cursor()

	# Query
	query = """
	SELECT id FROM classes
	WHERE class_code = %s
	"""

	# Execute query
	values = (class_code)
	cur.execute(query, values)
	conn.commit()

	# get the class id
	class_id = cur.fetchone()[0]

	# Query
	query = """
	SELECT associated_classes FROM accounts
	WHERE id = %s
	"""

	# Execute query
	values = (user_id)
	cur.execute(query, values)
	conn.commit()

	# Get the classes student is currently registered for
	current_classes = json.loads(cur.fetchone()[0])
	current_classes.append(class_id)

	# Query
	query = """
	UPDATE accounts 
	SET associated_classes = %s
	WHERE id = %s
	"""

	# Execute query
	values = (json.dumps(obj=current_classes), user_id)
	cur.execute(query, values)
	conn.commit()

	# Close 
	cur.close()
	conn.close()

def add_question(class_id, user_id, question_text, datasources, scored_terms):
	"""
	Adds a new question for the given question

	:param: int class_id: Unique identifier for the class
	:param: int user_id: Unique identifier for the user
	:param: str question_text: Question title that will be asked of student
	:param: list datasources: List of urls to be used to retrieve question answer
	:param: list scored_terms: List of term, score tuples
	:returns: Unique id of question
	:rtype: int
	"""

	# Create a connection
	conn = make_connection()

	# Create a cursor
	cur = conn.cursor()

	# Query
	query = """
	INSERT INTO questions
	SET class_id = %s, author_id = %s, datasources = %s, scored_terms = %s, question_title = %s
	RETURNING id
	"""

	# Execute query
	values = (class_id, user_id, json.dumps(datasources), json.dumps(scored_terms), question_text)
	cur.execute(query, values)
	conn.commit()

	question_id = cur.fetchone()[0]

	# close
	cur.close()
	conn.close()

	return question_id

def answer_question(user_id, question_id, student_response, response_score):
	"""
	Adds the student response to a given question to the student responses table.

	:param: int user_id: Unique identifier for the student
	:param: int question_id: Unique identifier for the question
	:param: str student_response: Student's given response as raw text
	:param: float response_score: Student's score for their given response
	"""

	# Create a connection
	conn = make_connection()

	# Create a cursor
	cur = conn.cursor()

	## Get the current responses

	# Query
	query = """
	SELECT raw_responses, response_scores
	FROM student_responses
	WHERE student_id = %s
	"""

	# Execute
	values = (user_id)
	cur.execute(query, values)
	conn.commit()

	# Get vals
	existing_responses = json.loads(cur.fetchall()[0])
	existing_scores = json.loads(cur.fetchall()[1])

	# Update dicts
	existing_responses[question_id] = student_response
	existing_scores[question_id] = response_score

	# Query
	query = """
	UPDATE student_responses
	SET raw_responses = %s, response_scores = %s
	WHERE student_id = %s
	"""

	# Execute
	values = (json.dumps(existing_responses), json.dumps(existing_scores), user_id)
	cur.execute(query, values)
	conn.commit()

	cur.close()
	conn.close()

def get_user_classes(user_id):
	""" 
	Get all associated classes for a given user

	:param: int user_id: Unique identifier for the student
	:returns: Dictionary of all class information keyed by class id
	:rtype: dict
	"""

	# Create a connection
	conn = make_connection()

	# Create a cursor
	cur = conn.cursor()

	# Query
	query = """
	SELECT associated_classes
	FROM accounts
	WHERE id = %s
	"""

	# Execute query
	values = (user_id)
	cur.execute(query, values)
	conn.commit()


	# class_ids
	class_ids = cur.fetchall()

	if len(class_ids) > 0:

		all_classes = {}

		# Simplify back into a single query
		for c in class_ids:

			# query 
			query = """
			SELECT * 
			FROM classes
			WHERE id = %s
			"""

			# execute
			values = (c)
			cur.execute(query, values)
			conn.commit()

			tmp = cur.fetchall()
			tmp_dict = {}
			tmp_dict["class_code"] = tmp[1]
			tmp_dict["class_creator_id"] = tmp[2]
			tmp_dict["class_name"] = tmp[3]
			tmp_dict["class_subject"] = tmp[4]
			tmp_dict["class_topics"] = json.loads(tmp[5])
			all_classes[c] = tmp_dict

		cur.close()
		conn.close()
		return all_classes

	else:
		cur.close()
		conn.close()
		return None

def get_class_questions(class_id):
	"""
	Gets all associated questions for a given class

	:param: int class_id: unique identifier for the class
	:returns: Dictionary of all question information keyed by the question id
	:rtype: dict
	"""

	# Create a connection
	conn = make_connection()

	# Create a cursor
	cur = conn.cursor()

	query = """
	SELECT * 
	FROM questions
	WHERE class_id = %s
	"""

	# execute
	values = (class_id)
	cur.execute(query, values)
	conn.commit()

	question_data = cur.fetchall()

	if len(question_data) > 0:
		
		# reform
		question_dict = {}
		for question in question_data:
			question_dict[question[0]] = {}
			question_dict[question[0]]['title'] = questions[2]
			question_dict[question[0]]['datasources'] = json.loads(questions[3])
			question_dict[question[0]]['scored_terms'] = json.loads(questions[4])
			question_dict[question[0]]['author_id'] = questions[5]

		cur.close()
		conn.close()
		return question_dict

	else:
		cur.close()
		conn.close()
		return None

def get_single_class(class_id):
	"""
	Get all associated information for a given class

	:param: int class_id: unique identifier for a class
	:returns: Dictionary of all class information for given class id keyed by class id
	:rtype: dict
	"""

	# Create a connection
	conn = make_connection()

	# Create a cursor
	cur = conn.cursor()

	# query 
	query = """
	SELECT * 
	FROM classes
	WHERE id = %s
	"""

	# execute
	values = (class_id)
	cur.execute(query, values)
	conn.commit()


	tmp = cur.fetchall()

	if len(tmp) > 0:
		tmp_dict = {}
		tmp_dict["class_code"] = tmp[1]
		tmp_dict["class_creator_id"] = tmp[2]
		tmp_dict["class_name"] = tmp[3]
		tmp_dict["class_subject"] = tmp[4]
		tmp_dict["class_topics"] = json.loads(tmp[5])

		cur.close()
		conn.close()
		return tmp_dict

	else:
		cur.close()
		conn.close()
		return None

def get_question_answer(user_id, question_id):
	"""
	Get the student response and score for a given question and user

	:param: int user_id: Unique identifier for the user
	:param: int question_id: Unique identifier for the question
	:returns: Tuple of user response information (response, score)
	:rtype: tuple
	"""

	# Create a connection
	conn = make_connection()

	# Create a cursor
	cur = conn.cursor()

	# Query
	query = """
	SELECT raw_responses, response_scores
	FROM student_responses
	WHERE student_id = %s
	"""

	# Execute
	values = (user_id)
	cur.execute(query, values)
	conn.commit()

	response = json.loads(cur.fetchall()[0])[question_id]
	score = json.loads(cur.fetchall()[1])[question_id]

	cur.close()
	conn.close()

	return (response, score)

def get_single_question(question_id):
	"""
	Get all associated information for a given question

	:param: int question_id: Unique identifier for the question
	:returns: Dictionary of all question informaton for a given question keyed by question id
	:rtype: dict
	"""

	# Create a connection
	conn = make_connection()

	# Create a cursor
	cur = conn.cursor()

	# Query
	query = """
	SELECT * 
	FROM questions
	WHERE id = %s
	"""

	# execute
	values = (question_id)
	cur.execute(query, values)
	conn.commit()

	question_data = cur.fetchone()

	if len(question_data) > 0:
		
		# reform
		question_dict = {}
		
		question_dict[question_id] = {}
		question_dict[question_id]['title'] = question_data[2]
		question_dict[question_id]['datasources'] = json.loads(question_data[3])
		question_dict[question_id]['scored_terms'] = json.loads(question_data[4])
		question_dict[question_id]['author_id'] = question_data[5]

		cur.close()
		conn.close()
		return question_dict

	else:
		cur.close()
		conn.close()
		return None

def get_user_info(email):
	"""
	Get all user information for a given email

	:param: str email: Email for desired user
	:returns: Dictionary of user information keyed by user_id
	:rtype: dict
	"""

	# Create a connection
	conn = make_connection()

	# Create a cursor
	cur = conn.cursor()

	# Query
	query = """
	SELECT * 
	FROM accounts
	WHERE email = %s
	"""

	# Execute
	values = (email)
	cur.execute(query, values)
	conn.commit()

	user_data = cur.fetchone()

	if len(user_data) > 0:
		user_info_dict = {}
		user_info_dict[user_data[0]] = {}
		user_info_dict[user_data[0]]['first_name'] = user_data[1]
		user_info_dict[user_data[0]]['last_name'] = user_data[2]
		user_info_dict[user_data[0]]['is_teacher'] = user_data[3]
		user_info_dict[user_data[0]]['is_student'] = user_data[4]
		user_info_dict[user_data[0]]['email'] = user_data[5]
		user_info_dict[user_data[0]]['affiliation'] = user_data[6]
		user_info_dict[user_data[0]]['associated_classes'] = json.loads(user_data[7])
		user_info_dict[user_data[0]]['username'] = user_data[8]

		cur.close()
		conn.close()
		return user_info_dict

	else:
		cur.close()
		conn.close()
		return None








