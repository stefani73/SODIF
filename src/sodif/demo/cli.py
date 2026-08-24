"""Console entry point for the deterministic flight."""

from json import dumps

from sodif.demo.runner import run_default_flight


def main() -> None:
    report = run_default_flight().model_dump(
        mode="json",
        exclude_computed_fields=True,
    )
    print(dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
