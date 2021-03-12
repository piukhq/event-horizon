from sqlalchemy.ext.automap import automap_base

from app.db.session import engine

Base = automap_base()
Base.prepare(engine, reflect=True)


# get models from Base mapping
User = Base.classes.user
UserProfile = Base.classes.userprofile
