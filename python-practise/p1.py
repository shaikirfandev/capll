#WAP to store the user fav movies in a list and print them in reverse order.


Fav_movies = [""] * 3
n = 0 

while(Fav_movies.length > n):
    Fav_movies[n] = input("Enter Fav top 3 movies name")
    n+= 1

print("Your Fav movies in reverse order are:")
for i in range(len(Fav_movies)-1, -1, -1):
    print(Fav_movies[i])





