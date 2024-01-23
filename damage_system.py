import random


def fightWithACharacter(playerAccuracy, playerHandling, playerDamage, playerFireRate, playerBulletProof, playerHealth, enemyAccuracy, enemyHandling, enemyDamage, enemyFireRate, enemyBulletProof, enemyHealth):
    playerHealthDuringFight = playerHealth
    enemyHealthDuringFight = enemyHealth

    while(enemyHealthDuringFight > 0 and playerHealthDuringFight > 0):
        playerHealthDuringFight = round(playerHealthDuringFight - calculateDMG(enemyAccuracy, enemyHandling, enemyDamage, enemyFireRate, enemyBulletProof))
        enemyHealthDuringFight = round(enemyHealthDuringFight - calculateDMG(playerAccuracy, playerHandling, playerDamage, playerFireRate, playerBulletProof))

    return playerHealthDuringFight, enemyHealthDuringFight


def calculateDMG(accuracy, handling, damage, fireRate, bulletProof):
    return rawDMGOutPut(accuracy, handling, damage, fireRate) * (bulletProof/10)


def rawDMGOutPut(accuracy, handling, damage, fireRate):
    return lesserOrGreater(accuracy) * (handling + damage) * (fireRate/10)


def lesserOrGreater(accuracy):
    randomNumber = round(random.uniform(0, 1.1), 1)
    generatedNumber = accuracy / 10
    if generatedNumber >= randomNumber:
        return 1
    else:
        return 0

