#include <stdio.h>
#include "weak.h"

int weak_number __attribute__((weak)) = 50;

void __attribute__((weak)) print_weak(char *str, int times)
{
	while (times--)
	{
		printf("weak1: %s", str);
	}
}
