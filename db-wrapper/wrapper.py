import json
import psycopg2
import os
import json

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
		SET creator_id = %s, class_name = %s, subject = %s, topics = %s 
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
	SELECT classes FROM accounts
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
	SET classes = %s
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

	
