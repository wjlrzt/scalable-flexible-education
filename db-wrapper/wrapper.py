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


def add_account(first_name, last_name, is_teacher, is_student, email, affiliation):
	"""
	Adds a new account entry to the accounts table in the database

	:param: str first_name: First name of the new account user.
	:param: str last_name: Last name of the new account user.
	:param: bool is_teacher: Boolean indicator whether a person is a teacher or not.
	:param: bool is_student: Boolean indicator whether a person is a student or not.
	:param: str email: Email of the new account user.
	:param: str affiliation: Academic affiliation of the new user.
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
		SET first_name = %s, last_name = %s, is_teacher = %s, is_student = %s, email = %s, affiliation = %s
		RETURNING id
		"""

		# Make query commit
		values = (first_name, last_name, is_teacher, is_student, email, affiliation)
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

	