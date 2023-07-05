from booking import booking_main
from maeva import maeva_main
from camping import camping_main
from tools.args import main_arguments
from yelloh import yelloh_main


if __name__ == "__main__":
    args = main_arguments()

    if args.platform and args.platform == 'booking':
        booking_main()
    if args.platform and args.platform == 'maeva':
        maeva_main()
    if args.platform and args.platform == 'campings':
        camping_main()
    if args.platform and args.platform == 'yellohvillage':
        yelloh_main()
