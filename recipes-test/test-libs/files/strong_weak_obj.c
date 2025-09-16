#include <stdio.h>
#include "strong_weak_obj.h"

int weak_number __attribute__((weak)) = 50;

void print_strong(char *str, int times)
{
	while (times--)
	{
		printf("%s", str);
	}
}

void __attribute__((weak)) print_weak(char *str, int times)
{
	while (times--)
	{
		printf("weak1: %s", str);
	}
}