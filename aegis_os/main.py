from aegis_os.core.kernel import Kernel


def main():
    print("Initializing Aegis OS...")

    kernel = Kernel()

    kernel.boot()


if __name__ == "__main__":
    main()