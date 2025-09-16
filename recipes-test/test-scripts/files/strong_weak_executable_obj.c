#include <stdio.h>
#include "strong_weak_obj.h"

extern int weak_number;

int main()
{
	print_strong("print_strong is a strong symbol",3);
    print_weak("print_weak is a weak symbol",3);
    printf("Weak symbol number: %d", weak_number);
	return 0;
}
