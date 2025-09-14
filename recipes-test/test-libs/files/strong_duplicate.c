#include <stdio.h>
#include "strong.h"

void print_strong(char *str, int times)
{
	while (times--)
	{
		printf("%s", str);
	}
}
