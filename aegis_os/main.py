import json

from aegis_os.core.kernel import Kernel
from aegis_os.core.runtime import Runtime


def main() -> None:
    print("Initializing Aegis OS...")

    kernel = Kernel()
    kernel.boot()

    runtime = Runtime(kernel)
    runtime.start()

    print("\nStarting canonical cognitive operation...")

    result = kernel.process_task(
        "Research Aegis autonomous intelligence",
        "aegis-main-demo-1",
        execute=True,
    )

    print("\nAegis Canonical Result:")
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
