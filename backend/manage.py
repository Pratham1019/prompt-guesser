import argparse
import asyncio
import sys
from datetime import date

from app.database import SessionLocal
from app.services.generation import ChallengeGenerationService
from app.services.scheduler import ChallengeSchedulerService


async def cmd_status(args):
    """Previews scheduler status and challenge buffer compliance."""
    try:
        async with SessionLocal() as db:
            scheduler = ChallengeSchedulerService(db)
            status = await scheduler.get_buffer_status()

            print("\n=== DAILY CHALLENGE SCHEDULER STATUS ===")
            print(f"Publication Timezone : {scheduler.timezone}")
            print(f"Current Local Date   : {status['today']}")
            print(f"Configured Buffer    : {status['configured_buffer']} days")
            print("-----------------------------------------")
            print(f"Active Future Count  : {status['active_count']}")
            print(f"Failed Future Count  : {status['failed_count']}")
            print(f"Missing Future Count : {status['missing_count']}")
            print("-----------------------------------------")

            if status["active_dates"]:
                print("Active Scheduled Dates:")
                for d in status["active_dates"]:
                    print(f"  [OK] {d}")
            else:
                print("Active Scheduled Dates: None")

            if status["failed_dates"]:
                print("Failed Future Dates:")
                for d in status["failed_dates"]:
                    print(f"  [ERROR] {d}")

            if status["missing_dates"]:
                print("Missing Future Dates:")
                for d in status["missing_dates"]:
                    print(f"  [WARNING] {d}")
            print("=========================================\n")
    except Exception as e:
        print(f"[ERROR] Status check failed: {e}", file=sys.stderr)
        sys.exit(1)


async def cmd_populate(args):
    """Audits buffer status and generates challenges to satisfy buffer size."""
    try:
        async with SessionLocal() as db:
            scheduler = ChallengeSchedulerService(db)
            print("Auditing buffer and generating challenges. Please wait...")
            generated = await scheduler.populate_buffer()
            if generated:
                print(f"[OK] Completed. Generated {len(generated)} challenges.")
                for c in generated:
                    # Guard prompt in case it is still None/Failed
                    prompt_text = c.prompt[:60] if c.prompt else "[No Prompt Generated]"
                    print(
                        f"  - ID {c.id}: Scheduled for {c.publish_date} (Prompt: '{prompt_text}...')"
                    )
            else:
                print("[OK] Buffer is already fully compliant. No challenges needed.")
    except Exception as e:
        print(f"[ERROR] Buffer population failed: {e}", file=sys.stderr)
        sys.exit(1)


async def cmd_publish_today(args):
    """Publishes today's scheduled challenge."""
    try:
        async with SessionLocal() as db:
            scheduler = ChallengeSchedulerService(db)
            print("Publishing today's scheduled challenge...")
            challenge = await scheduler.publish_today_challenge()
            if challenge:
                print(
                    f"[OK] Success. Challenge ID {challenge.id} published for {challenge.publish_date}."
                )
            else:
                print("[ERROR] Publication aborted: no scheduled challenge found for today's date.")
    except Exception as e:
        print(f"[ERROR] Publication failed: {e}", file=sys.stderr)
        sys.exit(1)


async def cmd_generate_date(args):
    """Generates a challenge for a specific date."""
    try:
        target_date = date.fromisoformat(args.date)
    except ValueError:
        print(f"[ERROR] Invalid date format '{args.date}'. Must be YYYY-MM-DD.", file=sys.stderr)
        sys.exit(1)

    try:
        async with SessionLocal() as db:
            gen_svc = ChallengeGenerationService(db)
            print(f"Generating challenge for specific date {target_date}...")
            challenge = await gen_svc.generate_daily_challenge(target_date)
            print(
                f"[OK] Success. Challenge ID {challenge.id} created for {challenge.publish_date}."
            )
    except Exception as e:
        print(f"[ERROR] Generation failed: {e}", file=sys.stderr)
        sys.exit(1)


async def cmd_regenerate_failed(args):
    """Regenerates a failed challenge by its database ID."""
    try:
        async with SessionLocal() as db:
            gen_svc = ChallengeGenerationService(db)
            print(f"Attempting to regenerate failed challenge ID {args.id}...")
            challenge = await gen_svc.regenerate_failed_challenge(args.id)
            print(
                f"[OK] Success. Challenge ID {challenge.id} regenerated and scheduled for {challenge.publish_date}."
            )
    except Exception as e:
        print(f"[ERROR] Regeneration failed: {e}", file=sys.stderr)
        sys.exit(1)


async def cmd_cleanup(args):
    """Cleans up expired challenges and associated storage objects."""
    try:
        async with SessionLocal() as db:
            scheduler = ChallengeSchedulerService(db)
            print("Running cleanup of expired challenges. Please wait...")
            cleaned_ids = await scheduler.run_cleanup()
            if cleaned_ids:
                print(
                    f"[OK] Completed. Successfully deleted {len(cleaned_ids)} expired challenges (IDs: {cleaned_ids})."
                )
            else:
                print("[OK] Completed. No expired challenges found.")
    except Exception as e:
        print(f"[ERROR] Cleanup failed: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="CLI tool to manage Daily Challenge generation and scheduling operations."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # status
    subparsers.add_parser("status", help="Preview scheduler status and buffer compliance.")

    # populate
    subparsers.add_parser("populate", help="Audit buffer and generate missing future challenges.")

    # publish-today
    subparsers.add_parser("publish-today", help="Publish today's scheduled challenge.")

    # cleanup
    subparsers.add_parser("cleanup", help="Clean up expired challenges and storage files.")

    # generate-date
    gen_parser = subparsers.add_parser(
        "generate-date", help="Generate a challenge for a specific date."
    )
    gen_parser.add_argument("--date", required=True, help="Target date in YYYY-MM-DD format.")

    # regenerate-failed
    regen_parser = subparsers.add_parser(
        "regenerate-failed", help="Regenerate a failed challenge by ID."
    )
    regen_parser.add_argument(
        "--id", type=int, required=True, help="Database ID of the failed challenge."
    )

    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    try:
        if args.command == "status":
            loop.run_until_complete(cmd_status(args))
        elif args.command == "populate":
            loop.run_until_complete(cmd_populate(args))
        elif args.command == "publish-today":
            loop.run_until_complete(cmd_publish_today(args))
        elif args.command == "cleanup":
            loop.run_until_complete(cmd_cleanup(args))
        elif args.command == "generate-date":
            loop.run_until_complete(cmd_generate_date(args))
        elif args.command == "regenerate-failed":
            loop.run_until_complete(cmd_regenerate_failed(args))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(130)


if __name__ == "__main__":
    main()
