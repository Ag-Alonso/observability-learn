weight = 4.8

#Ground cost

if weight <= 2:
  ground_cost = 20 + 1.50 * weight
elif weight <= 6:
  ground_cost = 20 + 3 * weight
elif weight <= 10:
  ground_cost = 20 + 4 * weight
elif weight > 10:
  ground_cost = 20 + 4.75 * weight

print ("Ground cost")
print (ground_cost)

#Ground premium cost

ground_premium_cost = 125
print ("Ground Premium cost")
print (ground_premium_cost)


#Drone cost

if weight <= 2:
  drone_cost = 4.5 * weight
elif weight  <= 6:
  drone_cost = 9 * weight
elif weight <= 10:
  drone_cost = 12 * weight
elif weight > 10:
  drone_cost = 14.25 * weight

print ("Drone cost")
print (drone_cost)


#Optional ---- Print the solution directly comparing variables.


if ground_cost < ground_premium_cost and ground_cost < drone_cost:
  cheapest_method = "Ground"
elif ground_premium_cost < ground_cost and ground_premium_cost < drone_cost:
  cheapest_method = "Premium"
elif drone_cost< ground_cost and drone_cost < ground_premium_cost:
  cheapest_method = "Drone"


print ("The cheapest method is " + cheapest_method)




