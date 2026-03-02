-- Reference Tables --
CREATE TABLE EntityType (
    EntityTypeID BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    -- GENERATED ALWAYS AS IDENTITY = modern PostgreSQL standard
    TypeName VARCHAR(100) NOT NULL
);
CREATE TABLE Source (
    SourceID BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    Name VARCHAR(255),
    URL TEXT
);
-- User Management --
CREATE TABLE Account (
    AccountID BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    Gmail VARCHAR(100) UNIQUE NOT NULL,
    Account_Role VARCHAR(255) NOT NULL DEFAULT 'user',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_account_gmail ON Account(Gmail);
-- Content --
CREATE TABLE Entity (
    EntityID BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    Name VARCHAR(255) NOT NULL,
    EntityTypeID BIGINT REFERENCES EntityType(EntityTypeID)
);
CREATE TABLE Article (
    ArticleID BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    Title TEXT,
    Content TEXT,
    SourceID BIGINT REFERENCES Source(SourceID),
    DatePublished DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
-- NLP Results --
CREATE TABLE EntityExtraction (
    EntityExtractionID BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ArticleID BIGINT REFERENCES Article(ArticleID) ON DELETE CASCADE,
    -- ON DELETE CASCADE = deleting an Article from Admin page removes related summaries, rankings, and notes automatically.
    EntityID BIGINT REFERENCES Entity(EntityID),
    Position INT,
    Frequency INT
);
CREATE TABLE EntityImportance (
    ImportanceID BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ExtractionID BIGINT REFERENCES EntityExtraction(EntityExtractionID) ON DELETE CASCADE,
    ImportanceScore FLOAT
);
CREATE TABLE RelationshipMap (
    RelationshipID BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ArticleID BIGINT REFERENCES Article(ArticleID) ON DELETE CASCADE,
    EntityA_ID BIGINT REFERENCES Entity(EntityID),
    EntityB_ID BIGINT REFERENCES Entity(EntityID)
);
-- User-specific Data --
CREATE TABLE UserArticle (
    UserArticleID BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    AccountID BIGINT REFERENCES Account(AccountID),
    ArticleID BIGINT REFERENCES Article(ArticleID) ON DELETE CASCADE,
    DateStored TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE Annotation (
    AnnotationID BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    AccountID BIGINT REFERENCES Account(AccountID),
    ArticleID BIGINT REFERENCES Article(ArticleID) ON DELETE CASCADE,
    Note TEXT
);
CREATE TABLE Summary (
    SummaryID BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    AccountID BIGINT REFERENCES Account(AccountID),
    ArticleID BIGINT REFERENCES Article(ArticleID) ON DELETE CASCADE,
    SummaryText TEXT
);