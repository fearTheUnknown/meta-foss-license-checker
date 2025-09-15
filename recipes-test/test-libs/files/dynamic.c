#include <stdio.h>
#include "dynamic.h"

void print_dynamic(char *str, int times)
{
	while (times--)
	{
		printf("dynamic: %s", str);
	}
}
