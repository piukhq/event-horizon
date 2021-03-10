import uuid
from functools import wraps

import msal
from flask import Flask, session, request, url_for, render_template, redirect, Response


class AzureSSO(object):
    def __init__(
            self, app: Flask,
    ):

        self._redirect_path = app.config["REDIRECT_PATH"]
        self._config_authority = app.config["AUTHORITY"]
        self._client_id = app.config["CLIENT_ID"]
        self.__client_secret = app.config["CLIENT_SECRET"]

        @app.route(self._redirect_path)
        def authorized():
            if request.args.get("state") != session.get("state"):
                return redirect(url_for("index"))  # No-OP. Goes back to Index page
            if "error" in request.args:  # Authentication/Authorization failure
                return render_template("auth_error.html", result=request.args)
            if request.args.get("code"):
                cache = self._load_cache()
                result = self._build_msal_app(cache=cache).acquire_token_by_authorization_code(
                    request.args["code"],
                    scopes=[],  # Misspelled scope would cause an HTTP 400 error here
                    redirect_uri=url_for("authorized", _external=True),
                )
                if "error" in result:
                    return render_template("auth_error.html", result=result)
                session["user"] = result.get("id_token_claims")
                # self._save_cache(cache)
            return redirect("/admin")

    @staticmethod
    def _load_cache():
        cache = msal.SerializableTokenCache()
        if session.get("token_cache"):
            cache.deserialize(session["token_cache"])
        return cache

    @staticmethod
    def _save_cache(cache):
        if cache.has_state_changed:
            session["token_cache"] = cache.serialize()

    def _build_msal_app(self, cache=None, authority=None):
        return msal.ConfidentialClientApplication(
            self._client_id,
            authority=authority or self._config_authority,
            client_credential=self.__client_secret,
            token_cache=cache,
        )

    def build_auth_url(self, authority=None, scopes=None, state=None):
        return self._build_msal_app(authority=authority).get_authorization_request_url(
            scopes or [], state=state or str(uuid.uuid4()), redirect_uri=url_for("authorized", _external=True)
        )

    def login_required(self, api: bool = False):
        def _d(f):
            @wraps(f)
            def _w(*args, **kwargs):
                if not session.get("user"):
                    session["state"] = str(uuid.uuid4())
                    if api:
                        return Response(
                            response='{"error": "Unauthenticated"}', status=400, mimetype="application/json"
                        )
                    return redirect(self.build_auth_url(scopes=[], state=session["state"]))
                return f(*args, **kwargs)

            return _w

        return _d
