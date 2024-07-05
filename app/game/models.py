from sqlmodel import Field, SQLModel


class PlayerPoint(SQLModel, table=True):
    """
    This class is a representative for Database Table and stores users score for each round of game
    Note: we only save the user submission if they give us the correct answer
    """

    # making the combination of below ids unique to ensure only one user can save the correct answer in database
    client_id: str = Field(primary_key=True)
    question_id: str = Field(primary_key=True)
    game_round_id: str = Field(primary_key=True)
