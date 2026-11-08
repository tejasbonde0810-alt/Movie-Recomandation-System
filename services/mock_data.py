"""
Mock data for offline demonstration, fallback, and automated testing.
Contains curated movies and TV shows across multiple languages (Hindi, English, Korean, Spanish, etc.)
with complete metadata (genres, keywords, cast, directors, overviews).
"""

MOCK_MOVIES = [
    {
        "id": 550,
        "title": "Fight Club",
        "original_language": "en",
        "release_date": "1999-10-15",
        "genre_ids": [18, 53],
        "vote_average": 8.4,
        "overview": "An insomniac office worker and a devil-may-care soap maker form an underground fight club that evolves into much more.",
        "credits": {
            "cast": [{"name": "Edward Norton"}, {"name": "Brad Pitt"}, {"name": "Helena Bonham Carter"}],
            "crew": [{"job": "Director", "name": "David Fincher"}]
        },
        "keywords": {"keywords": [{"name": "insomnia"}, {"name": "underground"}, {"name": "anti-establishment"}]}
    },
    {
        "id": 27205,
        "title": "Inception",
        "original_language": "en",
        "release_date": "2010-07-16",
        "genre_ids": [28, 878, 12],
        "vote_average": 8.4,
        "overview": "Cobb, a skilled thief who commits corporate espionage by infiltrating the subconscious of his targets, is offered a chance to regain his old life.",
        "credits": {
            "cast": [{"name": "Leonardo DiCaprio"}, {"name": "Joseph Gordon-Levitt"}, {"name": "Elliot Page"}],
            "crew": [{"job": "Director", "name": "Christopher Nolan"}]
        },
        "keywords": {"keywords": [{"name": "dream"}, {"name": "subconscious"}, {"name": "heist"}, {"name": "mind bending"}]}
    },
    {
        "id": 157336,
        "title": "Interstellar",
        "original_language": "en",
        "release_date": "2014-11-07",
        "genre_ids": [12, 18, 878],
        "vote_average": 8.4,
        "overview": "The adventures of a group of explorers who make use of a newly discovered wormhole to surpass the limitations on human space travel.",
        "credits": {
            "cast": [{"name": "Matthew McConaughey"}, {"name": "Anne Hathaway"}, {"name": "Jessica Chastain"}],
            "crew": [{"job": "Director", "name": "Christopher Nolan"}]
        },
        "keywords": {"keywords": [{"name": "space"}, {"name": "wormhole"}, {"name": "black hole"}, {"name": "time travel"}]}
    },
    {
        "id": 19404,
        "title": "Dilwale Dulhania Le Jayenge",
        "original_language": "hi",
        "release_date": "1995-10-20",
        "genre_ids": [35, 18, 10749],
        "vote_average": 8.5,
        "overview": "Raj and Simran meet on a trip across Europe and fall in love. When Raj learns Simran is promised to another, he follows her to India to win her family over.",
        "credits": {
            "cast": [{"name": "Shah Rukh Khan"}, {"name": "Kajol"}, {"name": "Amrish Puri"}],
            "crew": [{"job": "Director", "name": "Aditya Chopra"}]
        },
        "keywords": {"keywords": [{"name": "love"}, {"name": "family"}, {"name": "romance"}, {"name": "punjab"}]}
    },
    {
        "id": 20453,
        "title": "3 Idiots",
        "original_language": "hi",
        "release_date": "2009-12-25",
        "genre_ids": [18, 35],
        "vote_average": 8.0,
        "overview": "Two friends embark on a quest for a lost college buddy while reliving their college days and memories of an unconventional mentor who inspired them.",
        "credits": {
            "cast": [{"name": "Aamir Khan"}, {"name": "R. Madhavan"}, {"name": "Sharman Joshi"}, {"name": "Kareena Kapoor"}],
            "crew": [{"job": "Director", "name": "Rajkumar Hirani"}]
        },
        "keywords": {"keywords": [{"name": "college"}, {"name": "friendship"}, {"name": "education"}, {"name": "engineering"}]}
    },
    {
        "id": 579974,
        "title": "RRR",
        "original_language": "te",
        "release_date": "2022-03-25",
        "genre_ids": [28, 18],
        "vote_average": 7.8,
        "overview": "A fictional history of two legendary revolutionaries' journey away from home before they began fighting for their country in the 1920s.",
        "credits": {
            "cast": [{"name": "N.T. Rama Rao Jr."}, {"name": "Ram Charan"}, {"name": "Alia Bhatt"}, {"name": "Ajay Devgn"}],
            "crew": [{"job": "Director", "name": "S.S. Rajamouli"}]
        },
        "keywords": {"keywords": [{"name": "revolution"}, {"name": "friendship"}, {"name": "british empire"}, {"name": "action"}]}
    },
    {
        "id": 256040,
        "title": "Baahubali: The Beginning",
        "original_language": "te",
        "release_date": "2015-07-10",
        "genre_ids": [28, 12, 14],
        "vote_average": 7.6,
        "overview": "In the kingdom of Mahishmati, a young warrior discovers his true noble lineage and embarks on a journey to claim his rightful place.",
        "credits": {
            "cast": [{"name": "Prabhas"}, {"name": "Rana Daggubati"}, {"name": "Anushka Shetty"}],
            "crew": [{"job": "Director", "name": "S.S. Rajamouli"}]
        },
        "keywords": {"keywords": [{"name": "kingdom"}, {"name": "dynasty"}, {"name": "epic battle"}, {"name": "warrior"}]}
    },
    {
        "id": 496243,
        "title": "Parasite",
        "original_language": "ko",
        "release_date": "2019-05-30",
        "genre_ids": [35, 53, 18],
        "vote_average": 8.5,
        "overview": "All unemployed, Ki-taek's family takes peculiar interest in the wealthy and glamorous Parks for their livelihood until they get entangled in an unexpected incident.",
        "credits": {
            "cast": [{"name": "Song Kang-ho"}, {"name": "Lee Sun-kyun"}, {"name": "Cho Yeo-jeong"}],
            "crew": [{"job": "Director", "name": "Bong Joon-ho"}]
        },
        "keywords": {"keywords": [{"name": "social class"}, {"name": "satire"}, {"name": "wealth disparity"}, {"name": "con artist"}]}
    },
    {
        "id": 129,
        "title": "Spirited Away",
        "original_language": "ja",
        "release_date": "2001-07-20",
        "genre_ids": [16, 10751, 14],
        "vote_average": 8.5,
        "overview": "A young girl wandering into a world ruled by gods, witches, and spirits, and where humans are changed into beasts, must work to free herself and her parents.",
        "credits": {
            "cast": [{"name": "Rumi Hiiragi"}, {"name": "Miyu Irino"}, {"name": "Mari Natsuki"}],
            "crew": [{"job": "Director", "name": "Hayao Miyazaki"}]
        },
        "keywords": {"keywords": [{"name": "spirits"}, {"name": "magic"}, {"name": "bathhouse"}, {"name": "growing up"}]}
    },
    {
        "id": 769,
        "title": "GoodFellas",
        "original_language": "en",
        "release_date": "1990-09-19",
        "genre_ids": [18, 80],
        "vote_average": 8.5,
        "overview": "The story of Henry Hill and his life in the mafia, covering his relationship with his wife and his mob partners over three decades.",
        "credits": {
            "cast": [{"name": "Robert De Niro"}, {"name": "Ray Liotta"}, {"name": "Joe Pesci"}],
            "crew": [{"job": "Director", "name": "Martin Scorsese"}]
        },
        "keywords": {"keywords": [{"name": "mafia"}, {"name": "crime family"}, {"name": "organized crime"}]}
    },
    {
        "id": 857,
        "title": "Saving Private Ryan",
        "original_language": "en",
        "release_date": "1998-07-24",
        "genre_ids": [18, 36, 10752],
        "vote_average": 8.2,
        "overview": "As U.S. troops storm the beaches of Normandy, three brothers lie dead on the battlefield, with a fourth trapped behind enemy lines.",
        "credits": {
            "cast": [{"name": "Tom Hanks"}, {"name": "Matt Damon"}, {"name": "Tom Sizemore"}],
            "crew": [{"job": "Director", "name": "Steven Spielberg"}]
        },
        "keywords": {"keywords": [{"name": "world war ii"}, {"name": "normandy"}, {"name": "soldier"}, {"name": "rescue mission"}]}
    },
    {
        "id": 87827,
        "title": "Gangs of Wasseypur",
        "original_language": "hi",
        "release_date": "2012-06-22",
        "genre_ids": [28, 80, 18],
        "vote_average": 8.0,
        "overview": "A clash between Sultan and Shahid Khan leads to the expulsion of Khan from Wasseypur, and ignites a deadly blood feud spanning three generations.",
        "credits": {
            "cast": [{"name": "Manoj Bajpayee"}, {"name": "Nawazuddin Siddiqui"}, {"name": "Richa Chadha"}],
            "crew": [{"job": "Director", "name": "Anurag Kashyap"}]
        },
        "keywords": {"keywords": [{"name": "revenge"}, {"name": "gangster"}, {"name": "coal mafia"}, {"name": "blood feud"}]}
    }
]

MOCK_TV_SHOWS = [
    {
        "id": 1396,
        "name": "Breaking Bad",
        "original_language": "en",
        "first_air_date": "2008-01-20",
        "genre_ids": [18, 80],
        "vote_average": 8.9,
        "overview": "Walter White, a New Mexico chemistry teacher, is diagnosed with Stage III cancer and turns to manufacturing methamphetamine to secure his family's financial future.",
        "credits": {
            "cast": [{"name": "Bryan Cranston"}, {"name": "Aaron Paul"}, {"name": "Anna Gunn"}],
            "crew": [{"job": "Creator", "name": "Vince Gilligan"}]
        },
        "keywords": {"results": [{"name": "methamphetamine"}, {"name": "chemistry"}, {"name": "cartel"}, {"name": "anti-hero"}]}
    },
    {
        "id": 60059,
        "name": "Better Call Saul",
        "original_language": "en",
        "first_air_date": "2015-02-08",
        "genre_ids": [18, 80],
        "vote_average": 8.7,
        "overview": "Six years before he begins to represent Walter White, small-time lawyer Jimmy McGill transforms into criminal defense attorney Saul Goodman.",
        "credits": {
            "cast": [{"name": "Bob Odenkirk"}, {"name": "Rhea Seehorn"}, {"name": "Jonathan Banks"}],
            "crew": [{"job": "Creator", "name": "Vince Gilligan"}, {"job": "Creator", "name": "Peter Gould"}]
        },
        "keywords": {"results": [{"name": "lawyer"}, {"name": "con artist"}, {"name": "courtroom"}, {"name": "cartel"}]}
    },
    {
        "id": 81356,
        "name": "Sacred Games",
        "original_language": "hi",
        "first_air_date": "2018-07-06",
        "genre_ids": [80, 18, 9648],
        "vote_average": 8.4,
        "overview": "A link in their pasts leads an honest cop to a fugitive gang boss, whose cryptic warning spurs the officer to save Mumbai from cataclysm.",
        "credits": {
            "cast": [{"name": "Saif Ali Khan"}, {"name": "Nawazuddin Siddiqui"}, {"name": "Radhika Apte"}],
            "crew": [{"job": "Director", "name": "Anurag Kashyap"}, {"job": "Director", "name": "Vikramaditya Motwane"}]
        },
        "keywords": {"results": [{"name": "mumbai"}, {"name": "underworld"}, {"name": "conspiracy"}, {"name": "police corruption"}]}
    },
    {
        "id": 93405,
        "name": "Squid Game",
        "original_language": "ko",
        "first_air_date": "2021-09-17",
        "genre_ids": [28, 9648, 18],
        "vote_average": 7.8,
        "overview": "Hundreds of cash-strapped players accept a strange invitation to compete in children's games with high stakes and deadly survival consequences.",
        "credits": {
            "cast": [{"name": "Lee Jung-jae"}, {"name": "Park Hae-soo"}, {"name": "Jung Ho-yeon"}],
            "crew": [{"job": "Creator", "name": "Hwang Dong-hyuk"}]
        },
        "keywords": {"results": [{"name": "death game"}, {"name": "survival"}, {"name": "debt"}, {"name": "social critique"}]}
    },
    {
        "id": 71446,
        "name": "Money Heist",
        "original_language": "es",
        "first_air_date": "2017-05-02",
        "genre_ids": [80, 18],
        "vote_average": 8.2,
        "overview": "To carry out the biggest heist in history, a mysterious man called The Professor recruits a band of eight robbers who have a single characteristic: none of them has anything to lose.",
        "credits": {
            "cast": [{"name": "Úrsula Corberó"}, {"name": "Álvaro Morte"}, {"name": "Itziar Ituño"}],
            "crew": [{"job": "Creator", "name": "Álex Pina"}]
        },
        "keywords": {"results": [{"name": "heist"}, {"name": "hostage"}, {"name": "mint of spain"}, {"name": "mastermind"}]}
    },
    {
        "id": 95557,
        "name": "The Family Man",
        "original_language": "hi",
        "first_air_date": "2019-09-20",
        "genre_ids": [28, 18, 35],
        "vote_average": 8.3,
        "overview": "Srikant Tiwari is a middle-class man who also serves as a world-class spy, trying to balance his secretive, high-stakes career with his family life.",
        "credits": {
            "cast": [{"name": "Manoj Bajpayee"}, {"name": "Priyamani"}, {"name": "Sharib Hashmi"}],
            "crew": [{"job": "Creator", "name": "Raj & DK"}]
        },
        "keywords": {"results": [{"name": "spy"}, {"name": "counter-terrorism"}, {"name": "family life"}, {"name": "intelligence agent"}]}
    },
    {
        "id": 100088,
        "name": "The Last of Us",
        "original_language": "en",
        "first_air_date": "2023-01-15",
        "genre_ids": [18, 10765, 10759],
        "vote_average": 8.6,
        "overview": "Twenty years after modern civilization has been destroyed, Joel, a hardened survivor, is hired to smuggle Ellie, a 14-year-old girl, out of an oppressive quarantine zone.",
        "credits": {
            "cast": [{"name": "Pedro Pascal"}, {"name": "Bella Ramsey"}, {"name": "Gabriel Luna"}],
            "crew": [{"job": "Creator", "name": "Craig Mazin"}, {"job": "Creator", "name": "Neil Druckmann"}]
        },
        "keywords": {"results": [{"name": "post-apocalyptic"}, {"name": "pandemic"}, {"name": "survival"}, {"name": "fungal infection"}]}
    },
    {
        "id": 94605,
        "name": "Mirzapur",
        "original_language": "hi",
        "first_air_date": "2018-11-16",
        "genre_ids": [80, 18, 28],
        "vote_average": 8.2,
        "overview": "The iron-fisted Akhandanand Tripathi is a millionaire carpet exporter and the mafia don of Mirzapur. His son Munna is an unworthy, power-hungry heir.",
        "credits": {
            "cast": [{"name": "Pankaj Tripathi"}, {"name": "Ali Fazal"}, {"name": "Divyendu Sharma"}],
            "crew": [{"job": "Creator", "name": "Karan Anshuman"}, {"job": "Creator", "name": "Puneet Krishna"}]
        },
        "keywords": {"results": [{"name": "gangster"}, {"name": "power struggle"}, {"name": "uttar pradesh"}, {"name": "revenge"}]}
    },
    {
        "id": 66732,
        "name": "Stranger Things",
        "original_language": "en",
        "first_air_date": "2016-07-15",
        "genre_ids": [18, 10765, 9648],
        "vote_average": 8.6,
        "overview": "When a young boy vanishes, a small town uncovers a mystery involving secret experiments, terrifying supernatural forces and one strange little girl.",
        "credits": {
            "cast": [{"name": "Millie Bobby Brown"}, {"name": "Finn Wolfhard"}, {"name": "Winona Ryder"}],
            "crew": [{"job": "Creator", "name": "The Duffer Brothers"}]
        },
        "keywords": {"results": [{"name": "supernatural"}, {"name": "1980s"}, {"name": "upside down"}, {"name": "telepathy"}]}
    },
    {
        "id": 110316,
        "name": "Panchayat",
        "original_language": "hi",
        "first_air_date": "2020-04-03",
        "genre_ids": [35, 18],
        "vote_average": 8.5,
        "overview": "An engineering graduate takes up a job as a secretary of a Panchayat office in a remote rural village of Uttar Pradesh due to lack of better job opportunities.",
        "credits": {
            "cast": [{"name": "Jitendra Kumar"}, {"name": "Neena Gupta"}, {"name": "Raghubir Yadav"}],
            "crew": [{"job": "Creator", "name": "Chandan Kumar"}, {"job": "Director", "name": "Deepak Kumar Mishra"}]
        },
        "keywords": {"results": [{"name": "rural india"}, {"name": "village life"}, {"name": "bureaucracy"}, {"name": "comedy-drama"}]}
    }
]
