// Sample Neo4j Test Data - Movie Database
// This creates a small movie database with actors, directors, and movies

// Create Person nodes (Actors and Directors)
CREATE (keanu:Person {name: 'Keanu Reeves', born: 1964, occupation: 'Actor'})
CREATE (carrie:Person {name: 'Carrie-Anne Moss', born: 1967, occupation: 'Actor'})
CREATE (laurence:Person {name: 'Laurence Fishburne', born: 1961, occupation: 'Actor'})
CREATE (hugo:Person {name: 'Hugo Weaving', born: 1960, occupation: 'Actor'})
CREATE (lilly:Person {name: 'Lilly Wachowski', born: 1967, occupation: 'Director'})
CREATE (lana:Person {name: 'Lana Wachowski', born: 1965, occupation: 'Director'})
CREATE (tom:Person {name: 'Tom Hanks', born: 1956, occupation: 'Actor'})
CREATE (meg:Person {name: 'Meg Ryan', born: 1961, occupation: 'Actor'})
CREATE (nora:Person {name: 'Nora Ephron', born: 1941, occupation: 'Director'})
CREATE (leo:Person {name: 'Leonardo DiCaprio', born: 1974, occupation: 'Actor'})
CREATE (kate:Person {name: 'Kate Winslet', born: 1975, occupation: 'Actor'})
CREATE (james:Person {name: 'James Cameron', born: 1954, occupation: 'Director'})
CREATE (chris:Person {name: 'Christopher Nolan', born: 1970, occupation: 'Director'})
CREATE (joseph:Person {name: 'Joseph Gordon-Levitt', born: 1981, occupation: 'Actor'})
CREATE (ellen:Person {name: 'Elliot Page', born: 1987, occupation: 'Actor'})

// Create Movie nodes
CREATE (matrix:Movie {title: 'The Matrix', released: 1999, tagline: 'Welcome to the Real World', genre: 'Sci-Fi'})
CREATE (matrix2:Movie {title: 'The Matrix Reloaded', released: 2003, tagline: 'Free your mind', genre: 'Sci-Fi'})
CREATE (matrix3:Movie {title: 'The Matrix Revolutions', released: 2003, tagline: 'Everything that has a beginning has an end', genre: 'Sci-Fi'})
CREATE (sleepless:Movie {title: 'Sleepless in Seattle', released: 1993, tagline: 'What if someone you never met...', genre: 'Romance'})
CREATE (youvegot:Movie {title: "You've Got Mail", released: 1998, tagline: 'At odds in life... in love online', genre: 'Romance'})
CREATE (titanic:Movie {title: 'Titanic', released: 1997, tagline: 'Nothing on Earth could come between them', genre: 'Drama'})
CREATE (inception:Movie {title: 'Inception', released: 2010, tagline: 'Your mind is the scene of the crime', genre: 'Sci-Fi'})
CREATE (interstellar:Movie {title: 'Interstellar', released: 2014, tagline: 'Mankind was born on Earth', genre: 'Sci-Fi'})

// Create Studio nodes
CREATE (wb:Studio {name: 'Warner Bros.', founded: 1923, country: 'USA'})
CREATE (paramount:Studio {name: 'Paramount Pictures', founded: 1912, country: 'USA'})
CREATE (fox:Studio {name: '20th Century Fox', founded: 1935, country: 'USA'})

// Create Genre nodes
CREATE (scifi:Genre {name: 'Sci-Fi', description: 'Science Fiction'})
CREATE (romance:Genre {name: 'Romance', description: 'Romantic stories'})
CREATE (drama:Genre {name: 'Drama', description: 'Dramatic narratives'})
CREATE (action:Genre {name: 'Action', description: 'Action-packed movies'})

// Create ACTED_IN relationships
CREATE (keanu)-[:ACTED_IN {role: 'Neo', billing: 1}]->(matrix)
CREATE (keanu)-[:ACTED_IN {role: 'Neo', billing: 1}]->(matrix2)
CREATE (keanu)-[:ACTED_IN {role: 'Neo', billing: 1}]->(matrix3)
CREATE (carrie)-[:ACTED_IN {role: 'Trinity', billing: 2}]->(matrix)
CREATE (carrie)-[:ACTED_IN {role: 'Trinity', billing: 2}]->(matrix2)
CREATE (carrie)-[:ACTED_IN {role: 'Trinity', billing: 2}]->(matrix3)
CREATE (laurence)-[:ACTED_IN {role: 'Morpheus', billing: 3}]->(matrix)
CREATE (laurence)-[:ACTED_IN {role: 'Morpheus', billing: 3}]->(matrix2)
CREATE (laurence)-[:ACTED_IN {role: 'Morpheus', billing: 3}]->(matrix3)
CREATE (hugo)-[:ACTED_IN {role: 'Agent Smith', billing: 4}]->(matrix)
CREATE (hugo)-[:ACTED_IN {role: 'Agent Smith', billing: 4}]->(matrix2)
CREATE (hugo)-[:ACTED_IN {role: 'Agent Smith', billing: 4}]->(matrix3)
CREATE (tom)-[:ACTED_IN {role: 'Sam Baldwin', billing: 1}]->(sleepless)
CREATE (meg)-[:ACTED_IN {role: 'Annie Reed', billing: 2}]->(sleepless)
CREATE (tom)-[:ACTED_IN {role: 'Joe Fox', billing: 1}]->(youvegot)
CREATE (meg)-[:ACTED_IN {role: 'Kathleen Kelly', billing: 2}]->(youvegot)
CREATE (leo)-[:ACTED_IN {role: 'Jack Dawson', billing: 1}]->(titanic)
CREATE (kate)-[:ACTED_IN {role: 'Rose DeWitt Bukater', billing: 2}]->(titanic)
CREATE (leo)-[:ACTED_IN {role: 'Dom Cobb', billing: 1}]->(inception)
CREATE (joseph)-[:ACTED_IN {role: 'Arthur', billing: 2}]->(inception)
CREATE (ellen)-[:ACTED_IN {role: 'Ariadne', billing: 3}]->(inception)

// Create DIRECTED relationships
CREATE (lilly)-[:DIRECTED {year: 1999}]->(matrix)
CREATE (lana)-[:DIRECTED {year: 1999}]->(matrix)
CREATE (lilly)-[:DIRECTED {year: 2003}]->(matrix2)
CREATE (lana)-[:DIRECTED {year: 2003}]->(matrix2)
CREATE (lilly)-[:DIRECTED {year: 2003}]->(matrix3)
CREATE (lana)-[:DIRECTED {year: 2003}]->(matrix3)
CREATE (nora)-[:DIRECTED {year: 1993}]->(sleepless)
CREATE (nora)-[:DIRECTED {year: 1998}]->(youvegot)
CREATE (james)-[:DIRECTED {year: 1997}]->(titanic)
CREATE (chris)-[:DIRECTED {year: 2010}]->(inception)
CREATE (chris)-[:DIRECTED {year: 2014}]->(interstellar)

// Create PRODUCED_BY relationships
CREATE (matrix)-[:PRODUCED_BY {budget: 63000000}]->(wb)
CREATE (matrix2)-[:PRODUCED_BY {budget: 150000000}]->(wb)
CREATE (matrix3)-[:PRODUCED_BY {budget: 150000000}]->(wb)
CREATE (inception)-[:PRODUCED_BY {budget: 160000000}]->(wb)
CREATE (interstellar)-[:PRODUCED_BY {budget: 165000000}]->(paramount)
CREATE (titanic)-[:PRODUCED_BY {budget: 200000000}]->(paramount)
CREATE (titanic)-[:PRODUCED_BY {budget: 200000000}]->(fox)

// Create BELONGS_TO genre relationships
CREATE (matrix)-[:BELONGS_TO]->(scifi)
CREATE (matrix)-[:BELONGS_TO]->(action)
CREATE (matrix2)-[:BELONGS_TO]->(scifi)
CREATE (matrix2)-[:BELONGS_TO]->(action)
CREATE (matrix3)-[:BELONGS_TO]->(scifi)
CREATE (matrix3)-[:BELONGS_TO]->(action)
CREATE (sleepless)-[:BELONGS_TO]->(romance)
CREATE (youvegot)-[:BELONGS_TO]->(romance)
CREATE (titanic)-[:BELONGS_TO]->(drama)
CREATE (titanic)-[:BELONGS_TO]->(romance)
CREATE (inception)-[:BELONGS_TO]->(scifi)
CREATE (interstellar)-[:BELONGS_TO]->(scifi)

// Create KNOWS relationships between people
CREATE (keanu)-[:KNOWS {since: 1998}]->(carrie)
CREATE (keanu)-[:KNOWS {since: 1998}]->(laurence)
CREATE (carrie)-[:KNOWS {since: 1998}]->(laurence)
CREATE (tom)-[:KNOWS {since: 1990}]->(meg)
CREATE (leo)-[:KNOWS {since: 1996}]->(kate)
CREATE (lilly)-[:KNOWS {since: 1960}]->(lana)
CREATE (joseph)-[:KNOWS {since: 2009}]->(ellen)

// Create Review nodes and relationships
CREATE (r1:Review {rating: 5, comment: 'Mind-blowing visual effects!', date: date('1999-04-15')})
CREATE (r2:Review {rating: 4, comment: 'Great action sequences', date: date('1999-05-20')})
CREATE (r3:Review {rating: 5, comment: 'A timeless love story', date: date('1997-12-25')})
CREATE (r4:Review {rating: 5, comment: 'Incredible concept and execution', date: date('2010-07-20')})

CREATE (r1)-[:REVIEWS]->(matrix)
CREATE (r2)-[:REVIEWS]->(matrix)
CREATE (r3)-[:REVIEWS]->(titanic)
CREATE (r4)-[:REVIEWS]->(inception)

// Create indexes for better query performance
CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name);
CREATE INDEX movie_title IF NOT EXISTS FOR (m:Movie) ON (m.title);
CREATE INDEX movie_released IF NOT EXISTS FOR (m:Movie) ON (m.released);
CREATE INDEX studio_name IF NOT EXISTS FOR (s:Studio) ON (s.name);
CREATE INDEX genre_name IF NOT EXISTS FOR (g:Genre) ON (g.name);
