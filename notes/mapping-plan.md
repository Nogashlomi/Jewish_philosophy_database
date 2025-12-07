# Medieval Jewish Philosophy RDF Project - Class Diagram

## Classes

- HistoricalPerson → medieval/jewish philosopher
- HistoricalWork → text written by a HistoricalPerson
- ModernPerson → editor, translator, scholar
- ScholarlyWork → modern edition, translation, biography, study
- ScholarlyWorkType → edition, translation, biography, study

## Relationships

| From             | Property           | To                     | Notes |
|-----------------|-----------------|----------------------|------|
| HistoricalPerson | `schema:author`  | HistoricalWork        | medieval author wrote a text |
| ScholarlyWork    | `schema:author`  | ModernPerson          | modern scholar created edition/translation/biography/study |
| ScholarlyWork    | `jp:isEditionOf` | HistoricalWork        | edition/translation |
| ScholarlyWork    | `jp:isAboutPerson` | HistoricalPerson    | biography or study about a person |
| ScholarlyWork    | `jp:workType`    | ScholarlyWorkType     | edition, translation, biography, study |

## Diagram (ASCII / text)

[HistoricalPerson] --author--> [HistoricalWork] 
      ^
      |
  isAboutPerson
      |
[ScholarlyWork] --isEditionOf--> [HistoricalWork]
      |
      |--author--> [ModernPerson]
      |
      |--workType--> [ScholarlyWorkType]
