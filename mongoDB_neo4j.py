# Author: Long Huang
# Project 1: HetioNet Database Query Tool
# Resources: Project 1 Instructions, Google, StackOverflow, MongoDB Documentation, Neo4j Documentation, etc.
# Description: This script is a user case of querying the hetionet database in MongoDB and neo4j.
#				1. Create and populate the database in MongoDB and neo4j
#				2. Query information for a known disease by ID in MongoDB and neo4j
#				3. Find potential drugs for a new disease by ID in MongoDB and neo4j

import argparse
import csv
from pymongo import MongoClient
from neo4j import GraphDatabase


# Neo4j Client Class
class Neo4jClient:
	def __init__(self, uri, user, password):
		"""Initialize Neo4j client"""
		self._driver = GraphDatabase.driver(uri, auth=(user, password))

	def close(self):
		"""Close Neo4j client"""
		self._driver.close()

	def create_database(self):
		"""Create Neo4j database"""
		with self._driver.session() as session:
			session.write_transaction(self._create_database_tx)

	@staticmethod
	def _create_database_tx(tx):
		"""DO NOT USE!!! haven't test it yet, not sure if it works,
            not certain if manual upload to neo4j desktop vs.
            using this script to upload to neo4j are the same.
            concern: file not cleaned, unfamiliar with py2neo package"""
		"""Populate the Neo4j database"""
		# Clear existing nodes and relationships (CAUTION: This will remove all existing data)
		tx.run("MATCH (n) DETACH DELETE n")

		# Populate Nodes from nodes_test.tsv
		with open('nodes_test.tsv', mode='r') as file:
			csv_reader = csv.DictReader(file, delimiter='\t')
			for row in csv_reader:
				tx.run("CREATE (:Node {id: $id, name: $name, kind: $kind})",
					   id=row['id'], name=row['name'], kind=row['kind'])

		# Populate Edges from edges_test.tsv
		with open('edges_test.tsv', mode='r') as file:
			csv_reader = csv.DictReader(file, delimiter='\t')
			for row in csv_reader:
				tx.run("""
                MATCH (source:Node {id: $source}), (target:Node {id: $target})
                CREATE (source)-[:RELATES {metaedge: $metaedge}]->(target)
                """, source=row['source'], target=row['target'], metaedge=row['metaedge'])

		print("Neo4j database created and populated.")

	def query_disease_info_neo4j(self, disease_id):
		"""Given a disease id, return its name, drugs that treat it, genes that cause it, and anatomy that it affects"""
		with self._driver.session() as session:
			return session.execute_read(self._query_disease_info_tx, disease_id)

	# static method can be called on the class itself without instantiating the class
	@staticmethod
	def _query_disease_info_tx(tx, disease_id):
		"""Given a disease id, return its name, drugs that treat it, genes that cause it, and anatomy that it affects"""
		query = '''
        MATCH (d:Node {kind: "Disease", id: $disease_id})
        OPTIONAL MATCH (d)-[:RELATES {metaedge: "CtD"}]->(c:Node {kind: "Compound"})
        OPTIONAL MATCH (d)-[:RELATES {metaedge: "DdG"}]->(g:Node {kind: "Gene"})
        OPTIONAL MATCH (d)-[:RELATES {metaedge: "DlA"}]->(a:Node {kind: "Anatomy"})
        RETURN d.name AS Disease_Name, 
               collect(DISTINCT c.name) AS Drugs, 
               collect(DISTINCT g.name) AS Genes, 
               collect(DISTINCT a.name) AS Anatomy
        '''
		result = tx.run(query, disease_id=disease_id).single()
		return result.data()

	def find_potential_drugs_for_new_disease(self, disease_id):
		"""Given a disease id, return a list of drugs that can treat it"""
		with self._driver.session() as session:
			return session.execute_read(self._find_potential_drugs_tx, disease_id)

	@staticmethod
	def _find_potential_drugs_tx(tx, disease_id):
		"""Given a disease id, return a list of drugs that can treat it"""
		query = '''
        MATCH (d:Node {kind: "Disease", id: $disease_id})
        OPTIONAL MATCH (d)-[:RELATES {metaedge: "DlA"}]->(a:Node {kind: "Anatomy"})
        OPTIONAL MATCH (a)-[:RELATES {metaedge: "AdG"}]->(g:Node {kind: "Gene"})
        OPTIONAL MATCH (c:Node {kind: "Compound"})-[:RELATES {metaedge: "CuG"}]->(g)
        WHERE NOT EXISTS((c)-[:RELATES {metaedge: "CtD"}]->(d))
        RETURN collect(DISTINCT c.name) AS Compounds
        '''
		result = tx.run(query, disease_id=disease_id)
		return result.single()["Compounds"]


class MongoDBClient:
	def __init__(self, uri):
		"""Initialize MongoDB client"""
		self._client = MongoClient(uri)
		self._db = self._client['hetionet_db']
		self._nodes_collection = self._db['nodes']
		self._edges_collection = self._db['edges']

	def create_database(self):
		"""DO NOT USE!!! haven't test it yet, not sure if it works,
        i am not certain if manual upload to mongoDB compass vs.
        using this script to upload to mongoDB are the same.
        concern: file not cleaned error with csv reader
                 Don't know how to batch import with pymongo"""
		"""MongoDB version of create_database"""
		"""create database and collections, it clears the database if it exists"""
		db = self._client['hetionet_db']

		# Create or clear the nodes collection
		self._nodes_collection = db['nodes']
		self._nodes_collection.drop()

		# Populate the nodes collection from a TSV file
		with open('nodes_test.tsv', mode='r') as file:
			csvFile = csv.DictReader(file, delimiter='\t')
			for line in csvFile:
				self._nodes_collection.insert_one(line)

		# Create or clear the edges collection
		self._edges_collection = db['edges']
		self._edges_collection.drop()

		# Populate the edges collection from another TSV file
		with open('edges_test.tsv', mode='r') as file:
			csvFile = csv.DictReader(file, delimiter='\t')
			for line in csvFile:
				self._edges_collection.insert_one(line)

		print("Database created and populated.")

	def get_disease_name(self, disease_id):
		"""Given a disease id, return its name"""
		disease_info = self._nodes_collection.find_one({'id': disease_id})
		if disease_info:
			return disease_info['name']
		else:
			return None

	def get_drugs_for_disease(self, disease_id):
		"""Given a disease id, return a list of drugs that treat it"""
		related_edges = self._edges_collection.find({'source': disease_id, 'metaedge': 'CtD'})
		drug_names = []
		for edge in related_edges:
			drug_info = self._nodes_collection.find_one({'id': edge['target']})
			if drug_info:
				drug_names.append(drug_info['name'])
		return drug_names

	def get_genes_for_disease(self, disease_id):
		"""Given a disease id, return a list of genes that cause it"""
		related_edges = self._edges_collection.find({'source': disease_id, 'metaedge': 'DdG'})
		gene_names = []
		for edge in related_edges:
			gene_info = self._nodes_collection.find_one({'id': edge['target']})
			if gene_info:
				gene_names.append(gene_info['name'])
		return gene_names

	def get_anatomy_for_disease(self, disease_id):
		"""Given a disease id, return a list of anatomy that it affects"""
		related_edges = self._edges_collection.find({'source': disease_id, 'metaedge': 'DlA'})
		anatomy_names = []
		for edge in related_edges:
			anatomy_info = self._nodes_collection.find_one({'id': edge['target']})
			if anatomy_info:
				anatomy_names.append(anatomy_info['name'])
		return anatomy_names

	def query_disease_info(self, disease_id):
		"""Given a disease id, return its name, drugs that treat it, genes that cause it, and anatomy that it affects"""
		disease_name = self.get_disease_name(disease_id)  # Pass nodes_collection here
		if not disease_name:
			print("Disease ID not found.")
			return

		drug_names = self.get_drugs_for_disease(disease_id)
		gene_names = self.get_genes_for_disease(disease_id)
		anatomy_names = self.get_anatomy_for_disease(disease_id)

		print(f"Disease Name: {disease_name}")
		print(f"Drugs that can treat or palliate: {', '.join(drug_names) if drug_names else 'None'}")
		print(f"Genes that cause this disease: {', '.join(gene_names) if gene_names else 'None'}")
		print(f"Where this disease occurs: {', '.join(anatomy_names) if anatomy_names else 'None'}")

	def find_potential_drugs_for_new_disease(self, disease_id):
		"""Given a disease id, return a list of drugs that can treat it"""
		"""This function is very slow, so slow it may take hours to run
		due to the nature of document based database, 
		it is not suitable for this type of query, 
		but I will include it anyway for completeness"""
		related_gene_edges = list(
			self._edges_collection.find({'source': disease_id, 'metaedge': {'$in': ['DdG', 'DuG']}}))
		related_anatomy_edges = list(self._edges_collection.find({'source': disease_id, 'metaedge': 'DlA'}))

		gene_ids = [edge['target'] for edge in related_gene_edges]
		anatomy_ids = [edge['target'] for edge in related_anatomy_edges]

		related_compounds = list(
			self._edges_collection.find({'target': {'$in': gene_ids}, 'metaedge': {'$in': ['CdG', 'CuG']}}))

		potential_drugs = set()

		for compound_edge in related_compounds:
			compound_id = compound_edge['source']
			gene_id = compound_edge['target']
			action = 'CdG' if compound_edge['metaedge'] == 'CuG' else 'CuG'

			# Check if anatomy acts opposite to the disease on the gene
			anatomy_confirms = any(
				self._edges_collection.find_one({'source': anatomy_id, 'target': gene_id, 'metaedge': action}) for
				anatomy_id
				in
				anatomy_ids)

			if anatomy_confirms and not self._edges_collection.find_one(
					{'source': compound_id, 'target': disease_id, 'metaedge': 'CtD'}):
				compound_info = self._nodes_collection.find_one({'id': compound_id})
				if compound_info:
					potential_drugs.add(compound_info['name'])
		return list(potential_drugs)


# Main function
def main():
	# Argument parser for CLI
	parser = argparse.ArgumentParser(description="HetioNet Database Query Tool")
	parser.add_argument('--mongo_create_database', action='store_true',
						help='Create and populate the database using MongoDB')
	parser.add_argument('--mongo_disease_info', type=str,
						help='Query information for a known disease by ID')
	parser.add_argument('--mongo_find_drugs', type=str,
						help='Find potential drugs for a new disease by ID using MongoDB')

	parser.add_argument('--neo4j_create_database', action='store_true',
						help='Create and populate the Neo4j database')
	parser.add_argument('--neo4j_disease_info', type=str,
						help='Query information for a known disease by ID using Neo4j')
	parser.add_argument('--neo4j_find_drugs', type=str,
						help='Find potential drugs for a new disease by ID using Neo4j')

	args = parser.parse_args()

	# Initialize MongoDBClient
	mongo_client = MongoDBClient('mongodb://localhost:27017/')

	# Initialize Neo4jClient
	neo4j_client = Neo4jClient("bolt://localhost:7687", "neo4j", "12345678")

	# MongoDB operations
	if args.mongo_create_database:
		mongo_client.create_database()
	elif args.mongo_disease_info:
		mongo_client.query_disease_info(args.mongo_disease_info)
	elif args.mongo_find_drugs:
		drugs = mongo_client.find_potential_drugs_for_new_disease(args.mongo_find_drugs)
		print(f"Potential drugs for the disease (MongoDB): {', '.join(drugs) if drugs else 'None'}")

	# Neo4j operations
	elif args.neo4j_create_database:
		neo4j_client.create_database()
	elif args.neo4j_disease_info:
		disease_info = neo4j_client.query_disease_info_neo4j(args.neo4j_disease_info)
		print(f"Disease Name (Neo4j): {disease_info['Disease_Name']}")
		print(
			f"Drugs that can treat or palliate (Neo4j): {', '.join(disease_info['Drugs']) if disease_info['Drugs'] else 'None'}")
		print(
			f"Genes that cause this disease (Neo4j): {', '.join(disease_info['Genes']) if disease_info['Genes'] else 'None'}")
		print(
			f"Where this disease occurs (Neo4j): {', '.join(disease_info['Anatomy']) if disease_info['Anatomy'] else 'None'}")
	elif args.neo4j_find_drugs:
		drugs = neo4j_client.find_potential_drugs_for_new_disease(args.neo4j_find_drugs)
		print(f"Potential drugs for the disease (Neo4j): {', '.join(drugs) if drugs else 'None'}")
	else:
		print("No valid arguments provided.")


if __name__ == "__main__":
	main()
