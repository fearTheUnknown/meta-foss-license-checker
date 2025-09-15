#include <stdio.h>
#include "weak.h"

void __attribute__((weak)) print_weak(char *str, int times)
{
	while (times--)
	{
		printf("weak2: %s", str);
	}
}
