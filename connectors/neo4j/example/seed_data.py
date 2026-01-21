#!/usr/bin/env python3
"""Seed Neo4j test database with sample movie data."""

import os
import time
from neo4j import GraphDatabase


NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "testpassword123")


def wait_for_neo4j(driver, max_retries=30):
    """Wait for Neo4j to be ready."""
    for i in range(max_retries):
        try:
            with driver.session() as session:
                session.run("RETURN 1")
            print("Neo4j is ready!")
            return True
        except Exception as e:
            print(f"Waiting for Neo4j... ({i+1}/{max_retries})")
            time.sleep(2)
    return False


def clear_database(session):
    """Clear existing data."""
    session.run("MATCH (n) DETACH DELETE n")
    print("Cleared existing data")


def create_indexes(session):
    """Create indexes for better performance."""
    indexes = [
        "CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name)",
        "CREATE INDEX movie_title IF NOT EXISTS FOR (m:Movie) ON (m.title)",
        "CREATE INDEX movie_released IF NOT EXISTS FOR (m:Movie) ON (m.released)",
        "CREATE INDEX studio_name IF NOT EXISTS FOR (s:Studio) ON (s.name)",
        "CREATE INDEX genre_name IF NOT EXISTS FOR (g:Genre) ON (g.name)",
    ]
    for idx in indexes:
        session.run(idx)
    print("Created indexes")


def seed_data(session):
    """Seed the database with sample movie data."""
    
    # Create Person nodes
    persons = [
        {"name": "Keanu Reeves", "born": 1964, "occupation": "Actor"},
        {"name": "Carrie-Anne Moss", "born": 1967, "occupation": "Actor"},
        {"name": "Laurence Fishburne", "born": 1961, "occupation": "Actor"},
        {"name": "Hugo Weaving", "born": 1960, "occupation": "Actor"},
        {"name": "Lilly Wachowski", "born": 1967, "occupation": "Director"},
        {"name": "Lana Wachowski", "born": 1965, "occupation": "Director"},
        {"name": "Tom Hanks", "born": 1956, "occupation": "Actor"},
        {"name": "Meg Ryan", "born": 1961, "occupation": "Actor"},
        {"name": "Nora Ephron", "born": 1941, "occupation": "Director"},
        {"name": "Leonardo DiCaprio", "born": 1974, "occupation": "Actor"},
        {"name": "Kate Winslet", "born": 1975, "occupation": "Actor"},
        {"name": "James Cameron", "born": 1954, "occupation": "Director"},
        {"name": "Christopher Nolan", "born": 1970, "occupation": "Director"},
        {"name": "Joseph Gordon-Levitt", "born": 1981, "occupation": "Actor"},
        {"name": "Elliot Page", "born": 1987, "occupation": "Actor"},
    ]
    
    for p in persons:
        session.run(
            "CREATE (p:Person {name: $name, born: $born, occupation: $occupation})",
            p
        )
    print(f"Created {len(persons)} Person nodes")

    # Create Movie nodes
    movies = [
        {"title": "The Matrix", "released": 1999, "tagline": "Welcome to the Real World", "genre": "Sci-Fi"},
        {"title": "The Matrix Reloaded", "released": 2003, "tagline": "Free your mind", "genre": "Sci-Fi"},
        {"title": "The Matrix Revolutions", "released": 2003, "tagline": "Everything that has a beginning has an end", "genre": "Sci-Fi"},
        {"title": "Sleepless in Seattle", "released": 1993, "tagline": "What if someone you never met...", "genre": "Romance"},
        {"title": "You've Got Mail", "released": 1998, "tagline": "At odds in life... in love online", "genre": "Romance"},
        {"title": "Titanic", "released": 1997, "tagline": "Nothing on Earth could come between them", "genre": "Drama"},
        {"title": "Inception", "released": 2010, "tagline": "Your mind is the scene of the crime", "genre": "Sci-Fi"},
        {"title": "Interstellar", "released": 2014, "tagline": "Mankind was born on Earth", "genre": "Sci-Fi"},
    ]
    
    for m in movies:
        session.run(
            "CREATE (m:Movie {title: $title, released: $released, tagline: $tagline, genre: $genre})",
            m
        )
    print(f"Created {len(movies)} Movie nodes")

    # Create Studio nodes
    studios = [
        {"name": "Warner Bros.", "founded": 1923, "country": "USA"},
        {"name": "Paramount Pictures", "founded": 1912, "country": "USA"},
        {"name": "20th Century Fox", "founded": 1935, "country": "USA"},
    ]
    
    for s in studios:
        session.run(
            "CREATE (s:Studio {name: $name, founded: $founded, country: $country})",
            s
        )
    print(f"Created {len(studios)} Studio nodes")

    # Create Genre nodes
    genres = [
        {"name": "Sci-Fi", "description": "Science Fiction"},
        {"name": "Romance", "description": "Romantic stories"},
        {"name": "Drama", "description": "Dramatic narratives"},
        {"name": "Action", "description": "Action-packed movies"},
    ]
    
    for g in genres:
        session.run(
            "CREATE (g:Genre {name: $name, description: $description})",
            g
        )
    print(f"Created {len(genres)} Genre nodes")

    # Create ACTED_IN relationships
    acted_in = [
        ("Keanu Reeves", "The Matrix", "Neo", 1),
        ("Keanu Reeves", "The Matrix Reloaded", "Neo", 1),
        ("Keanu Reeves", "The Matrix Revolutions", "Neo", 1),
        ("Carrie-Anne Moss", "The Matrix", "Trinity", 2),
        ("Carrie-Anne Moss", "The Matrix Reloaded", "Trinity", 2),
        ("Carrie-Anne Moss", "The Matrix Revolutions", "Trinity", 2),
        ("Laurence Fishburne", "The Matrix", "Morpheus", 3),
        ("Laurence Fishburne", "The Matrix Reloaded", "Morpheus", 3),
        ("Laurence Fishburne", "The Matrix Revolutions", "Morpheus", 3),
        ("Hugo Weaving", "The Matrix", "Agent Smith", 4),
        ("Hugo Weaving", "The Matrix Reloaded", "Agent Smith", 4),
        ("Hugo Weaving", "The Matrix Revolutions", "Agent Smith", 4),
        ("Tom Hanks", "Sleepless in Seattle", "Sam Baldwin", 1),
        ("Meg Ryan", "Sleepless in Seattle", "Annie Reed", 2),
        ("Tom Hanks", "You've Got Mail", "Joe Fox", 1),
        ("Meg Ryan", "You've Got Mail", "Kathleen Kelly", 2),
        ("Leonardo DiCaprio", "Titanic", "Jack Dawson", 1),
        ("Kate Winslet", "Titanic", "Rose DeWitt Bukater", 2),
        ("Leonardo DiCaprio", "Inception", "Dom Cobb", 1),
        ("Joseph Gordon-Levitt", "Inception", "Arthur", 2),
        ("Elliot Page", "Inception", "Ariadne", 3),
    ]
    
    for actor, movie, role, billing in acted_in:
        session.run("""
            MATCH (p:Person {name: $actor}), (m:Movie {title: $movie})
            CREATE (p)-[:ACTED_IN {role: $role, billing: $billing}]->(m)
        """, {"actor": actor, "movie": movie, "role": role, "billing": billing})
    print(f"Created {len(acted_in)} ACTED_IN relationships")

    # Create DIRECTED relationships
    directed = [
        ("Lilly Wachowski", "The Matrix", 1999),
        ("Lana Wachowski", "The Matrix", 1999),
        ("Lilly Wachowski", "The Matrix Reloaded", 2003),
        ("Lana Wachowski", "The Matrix Reloaded", 2003),
        ("Lilly Wachowski", "The Matrix Revolutions", 2003),
        ("Lana Wachowski", "The Matrix Revolutions", 2003),
        ("Nora Ephron", "Sleepless in Seattle", 1993),
        ("Nora Ephron", "You've Got Mail", 1998),
        ("James Cameron", "Titanic", 1997),
        ("Christopher Nolan", "Inception", 2010),
        ("Christopher Nolan", "Interstellar", 2014),
    ]
    
    for director, movie, year in directed:
        session.run("""
            MATCH (p:Person {name: $director}), (m:Movie {title: $movie})
            CREATE (p)-[:DIRECTED {year: $year}]->(m)
        """, {"director": director, "movie": movie, "year": year})
    print(f"Created {len(directed)} DIRECTED relationships")

    # Create PRODUCED_BY relationships
    produced_by = [
        ("The Matrix", "Warner Bros.", 63000000),
        ("The Matrix Reloaded", "Warner Bros.", 150000000),
        ("The Matrix Revolutions", "Warner Bros.", 150000000),
        ("Inception", "Warner Bros.", 160000000),
        ("Interstellar", "Paramount Pictures", 165000000),
        ("Titanic", "Paramount Pictures", 200000000),
        ("Titanic", "20th Century Fox", 200000000),
    ]
    
    for movie, studio, budget in produced_by:
        session.run("""
            MATCH (m:Movie {title: $movie}), (s:Studio {name: $studio})
            CREATE (m)-[:PRODUCED_BY {budget: $budget}]->(s)
        """, {"movie": movie, "studio": studio, "budget": budget})
    print(f"Created {len(produced_by)} PRODUCED_BY relationships")

    # Create BELONGS_TO genre relationships
    belongs_to = [
        ("The Matrix", "Sci-Fi"), ("The Matrix", "Action"),
        ("The Matrix Reloaded", "Sci-Fi"), ("The Matrix Reloaded", "Action"),
        ("The Matrix Revolutions", "Sci-Fi"), ("The Matrix Revolutions", "Action"),
        ("Sleepless in Seattle", "Romance"),
        ("You've Got Mail", "Romance"),
        ("Titanic", "Drama"), ("Titanic", "Romance"),
        ("Inception", "Sci-Fi"),
        ("Interstellar", "Sci-Fi"),
    ]
    
    for movie, genre in belongs_to:
        session.run("""
            MATCH (m:Movie {title: $movie}), (g:Genre {name: $genre})
            CREATE (m)-[:BELONGS_TO]->(g)
        """, {"movie": movie, "genre": genre})
    print(f"Created {len(belongs_to)} BELONGS_TO relationships")

    # Create KNOWS relationships
    knows = [
        ("Keanu Reeves", "Carrie-Anne Moss", 1998),
        ("Keanu Reeves", "Laurence Fishburne", 1998),
        ("Carrie-Anne Moss", "Laurence Fishburne", 1998),
        ("Tom Hanks", "Meg Ryan", 1990),
        ("Leonardo DiCaprio", "Kate Winslet", 1996),
        ("Lilly Wachowski", "Lana Wachowski", 1960),
        ("Joseph Gordon-Levitt", "Elliot Page", 2009),
    ]
    
    for p1, p2, since in knows:
        session.run("""
            MATCH (a:Person {name: $p1}), (b:Person {name: $p2})
            CREATE (a)-[:KNOWS {since: $since}]->(b)
        """, {"p1": p1, "p2": p2, "since": since})
    print(f"Created {len(knows)} KNOWS relationships")

    # Create Review nodes
    reviews = [
        {"rating": 5, "comment": "Mind-blowing visual effects!", "movie": "The Matrix"},
        {"rating": 4, "comment": "Great action sequences", "movie": "The Matrix"},
        {"rating": 5, "comment": "A timeless love story", "movie": "Titanic"},
        {"rating": 5, "comment": "Incredible concept and execution", "movie": "Inception"},
    ]
    
    for r in reviews:
        session.run("""
            MATCH (m:Movie {title: $movie})
            CREATE (r:Review {rating: $rating, comment: $comment})-[:REVIEWS]->(m)
        """, r)
    print(f"Created {len(reviews)} Review nodes with relationships")


def print_summary(session):
    """Print database summary."""
    result = session.run("""
        MATCH (n) 
        RETURN labels(n)[0] as label, count(*) as count
        ORDER BY label
    """)
    print("\n=== Database Summary ===")
    for record in result:
        print(f"  {record['label']}: {record['count']} nodes")
    
    result = session.run("""
        MATCH ()-[r]->() 
        RETURN type(r) as type, count(*) as count
        ORDER BY type
    """)
    print("\n=== Relationships ===")
    for record in result:
        print(f"  {record['type']}: {record['count']} relationships")


def main():
    print(f"Connecting to Neo4j at {NEO4J_URI}...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    if not wait_for_neo4j(driver):
        print("Failed to connect to Neo4j")
        return
    
    with driver.session() as session:
        clear_database(session)
        create_indexes(session)
        seed_data(session)
        print_summary(session)
    
    driver.close()
    
    print("\n" + "="*50)
    print("Neo4j test database ready!")
    print("="*50)
    print(f"URI: {NEO4J_URI}")
    print(f"Username: {NEO4J_USER}")
    print(f"Password: {NEO4J_PASSWORD}")
    print("Database: neo4j")
    print("\nSample queries:")
    print("  MATCH (n:Person) RETURN n.name LIMIT 5")
    print("  MATCH (m:Movie) RETURN m.title, m.released")
    print("  MATCH (p:Person)-[:ACTED_IN]->(m:Movie) RETURN p.name, m.title")


if __name__ == "__main__":
    main()
