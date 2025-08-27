import os
from pathlib import Path

from dotenv import load_dotenv

from amigo_sdk import AmigoClient
from amigo_sdk.errors import AmigoError, NotFoundError
from amigo_sdk.models import (
    GetUsersParametersQuery,
    UserCreateInvitedUserRequest,
    UserUpdateUserInfoRequest,
)


def run() -> None:
    # Load env vars from examples/.env (shared by all examples)
    examples_env = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=examples_env)

    created_user_id: str | None = None
    created_user_email: str | None = None

    # Use a unique email so the example can be run repeatedly
    unique_suffix = f"{os.getpid()}-{int(os.times().elapsed * 1000)}"
    email = f"py-sdk-example-{unique_suffix}@example.com"

    with AmigoClient() as client:
        try:
            print("\n[1/5] Creating an invited user...")
            created = client.users.create_user(
                UserCreateInvitedUserRequest(
                    first_name="PY",
                    last_name="SDK-Example",
                    email=email,
                    role_name="DefaultUserRole",
                )
            )
            created_user_id = created.user_id
            created_user_email = email
            print("Created user_id:", created_user_id)

            print("\n[2/5] Updating the user profile...")
            if not created_user_id:
                raise RuntimeError("User was not created (no id received).")
            client.users.update_user(
                created_user_id,
                UserUpdateUserInfoRequest(
                    first_name="PY-Updated",
                    last_name="SDK-Example-Updated",
                    preferred_language={},
                    timezone={},
                ),
            )
            print("User updated.")

            print("\n[3/5] Listing users filtered by id...")
            by_id = client.users.get_users(
                GetUsersParametersQuery(user_id=[created_user_id])
            )
            by_id_count = len(getattr(by_id, "users", []) or [])
            print(
                "Users found by id:",
                by_id_count,
                "has_more:",
                getattr(by_id, "has_more", False),
            )

            print("\n[4/5] Listing users filtered by email...")
            if not created_user_email:
                raise RuntimeError("User email missing before list-by-email.")
            by_email = client.users.get_users(
                GetUsersParametersQuery(email=[created_user_email])
            )
            by_email_count = len(getattr(by_email, "users", []) or [])
            print(
                "Users found by email:",
                by_email_count,
                "has_more:",
                getattr(by_email, "has_more", False),
            )

            print("\n[5/5] Done. Cleaning up...")
        except AmigoError as err:
            print("[AmigoError]", err)
            raise SystemExit(1) from err
        except Exception as err:
            print("[Unexpected error]", err)
            raise SystemExit(1) from err
        finally:
            if created_user_id:
                try:
                    print("\nDeleting created user to keep the example re-runnable...")
                    client.users.delete_user(created_user_id)
                    print("Deleted user:", created_user_id)
                except NotFoundError:
                    print("User already deleted or not found.")
                except AmigoError as cleanup_err:
                    print("[Cleanup error]", cleanup_err)


if __name__ == "__main__":
    run()
