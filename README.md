# Project 1 Documentation

## Database Design 


#### Databases: Neo4j and MongoDB
- **MongoDB**: Capable of handling Query 1 but not efficient for Query 2 due to database limitations.
- **Neo4j**: Efficiently handles both Query 1 and Query 2, leveraging its graph capabilities especially for Query 2.

#### Data Model
- The data model consists of `Nodes` and `Edges`, represented in both MongoDB and Neo4j. Nodes can be of various `kinds` such as `Disease`, `Gene`, `Compound`, etc., and edges have `metaedges` to define the relationship types like `CtD`, `DdG`, etc.


#### Data Import
- Data is read from `nodes_test.tsv` and `edges_test.tsv` and can be imported using the command-line arguments `--mongo_create_database` and `--neo4j_create_database`.
- Note: The data import functionality is not fully tested. Manual upload(to database) is recommended.


### Query 1 

#### Neo4j
- Retrieves the disease's name, drugs that treat it, genes associated, and affected anatomy based on a given disease ID.
  - Command Line Interface `--mongo_disease_info`
  - Cypher language:
    ```
        Given a disease ID, you need the disease's name,
        drug names that can treat or palliate it,
        gene names that are associated with it,
        and the anatomy where it occurs.
    MATCH (d:Node {kind: "Disease"}) WHERE d.id = "Disease::DOID:0050156"
    OPTIONAL MATCH (d)-[r1:RELATES {metaedge: "CtD"}]->(c:Node {kind: "Compound"})
    OPTIONAL MATCH (d)-[r2:RELATES {metaedge: "DdG"}]->(g:Node {kind: "Gene"})
    OPTIONAL MATCH (d)-[r3:RELATES {metaedge: "DlA"}]->(a:Node {kind: "Anatomy"})
    RETURN d.name AS Disease_Name, 
           collect(DISTINCT c.name) AS Drugs, 
           collect(DISTINCT g.name) AS Genes, 
           collect(DISTINCT a.name) AS Anatomy
    ```
#### MongoDB
- Capable of performing the same functionality as Neo4j but with a less optimal performance.
  - Command Line Interface `--mongo_create_database`
  - MongoDB manual upload
### Query 2 

#### Neo4j
- Identifies potential compounds that can treat a new disease based on gene regulation criteria.
  - Command Line Interface `--neo4j_find_drugs`
  - Cypher language:
    ```
        Find all compounds that can treat a new disease based on specific gene regulation criteria.
        To achieve that, the query will need to identify compounds that up-regulate or down-regulate genes,
        and locations that do the opposite, where the disease occurs.
    MATCH (d:Node {kind: "Disease"}) WHERE d.id = "Disease::XLID:00001"
    MATCH (d)-[:RELATES {metaedge: "DlA"}]->(a:Node {kind: "Anatomy"})
    MATCH (a)-[r1:RELATES {metaedge: "AdG"}]->(g:Node {kind: "Gene"})
    MATCH (c:Node {kind: "Compound"})-[r2:RELATES]->(g)
    WHERE (r1.metaedge = "AdG" AND r2.metaedge IN ["CuG", "CdG"])
       OR (r1.metaedge = "AuG" AND r2.metaedge IN ["CdG", "CuG"])
    WITH d, c
    WHERE NOT (d)-[:RELATES {metaedge: "CtD"}]->(c)
    RETURN d.name AS Disease_Name, collect(DISTINCT c.name) AS Potential_Drugs
    ```
#### MongoDB
- This query is inefficient in MongoDB and could take hours to execute depending on hardware specifications.
  - Command Line Interface `--mongo_find_drugs`
  - MongoDB manual upload

### Command Line Interface (CLI) 

- Six main commands are provided for interaction:
  - `--mongo_create_database` USE WITH CAUTION
  - `--mongo_disease_info`    
  - `--mongo_find_drugs`      WILL TAKE FOREVER TO RUN
  - `--neo4j_create_database` USE WITH CAUTION
  - `--neo4j_disease_info`    
  - `--neo4j_find_drugs`      


### Readability and Structure

- The code is modular with classes for MongoDB and Neo4j clients, making it maintainable and extensible.

### Documentation

- Comments and docstrings are provided for functions to explain their functionality.


### Potential Improvements
- Separate read and write operations into different scripts.
- Robust error handling for database operations.
- Utilize database indexes for faster query execution.
- Implement data cleaning methods within 'create_database' functions for neo4j and mongoDB

### Usage Example
- Python Version: 3.11
- Required Packages: `argparse`, `csv`, `pymongo`, `neo4j`

#### Execution
Install desktop softwares for neo4j and mongoDB to manually upload the tsv files
Ensure `nodes_test.tsv` and `edges_test.tsv` are in the same directory.
Example usage: `python3 mongoDB_neo4j.py --neo4j_find_drugs Disease::XLID:00001`

### Note
Data import via the script is not fully tested. Manual upload is recommended.
