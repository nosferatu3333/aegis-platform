from aegis_os.core.kernel import Kernel
from aegis_os.core.runtime import Runtime


def main():

    print("Initializing Aegis OS...")


    kernel = Kernel()

    kernel.boot()


    runtime = Runtime(kernel)

    runtime.start()


    print("\nStarting cognitive operation...")


    result = kernel.process_goal(
        "Develop Aegis autonomous intelligence"
    )


    print("\nAegis Cognitive Result:")

    print(result)



if __name__ == "__main__":
    main()