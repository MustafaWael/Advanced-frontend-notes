# OOP Concepts for Low-Level Design Interviews

**Source:** https://www.hellointerview.com/learn/low-level-design/in-a-hurry/oop-concepts

## Overview

Where design principles teach you **how to think** about clean code, OOP concepts are the **mechanisms your language gives you** to implement those ideas. This is a focused refresher on the four core concepts that matter in interviews — for each: what it is, why interviewers care, and how it shows up in real LLD problems.

The four: **Encapsulation, Abstraction, Polymorphism, Inheritance.**

---

## Encapsulation

**What:** Keep an object's data private and let the object control how that data is used. Interact through methods instead of reaching in and changing internals directly.

**Why — predictability.** When `Account` owns its `balance` field and only allows modification through `deposit()` and `withdraw()`, you can enforce rules in those methods: prevent negative balances, log transactions, update related state. A public writable balance offers no guarantee those rules are followed.

**In interviews — a basic hygiene check:**
- Do your classes expose fields directly, or provide methods?
- Are you returning **references to mutable internal collections** callers can modify, or returning **copies**?

**Bad — public mutable state (anyone can modify `spots` directly):**

```python
class ParkingSpot:
    def occupy(self, vehicle: "Vehicle") -> None:
        ...

class Vehicle:
    def __init__(self, type_: str):
        self.type = type_

class ParkingLot:
    def __init__(self):
        self.spots: list[ParkingSpot] = []  # public, mutable
```

**Good — private state, behavior-exposing methods, defensive copies:**

```python
from typing import Optional

class ParkingLot:
    def __init__(self):
        self._spots: list[ParkingSpot] = []

    def park_vehicle(self, vehicle: Vehicle) -> bool:
        spot = self._find_available_spot(vehicle)
        if spot is None:
            return False
        spot.occupy(vehicle)
        return True

    def _find_available_spot(self, vehicle: Vehicle) -> Optional[ParkingSpot]:
        return self._spots[0] if self._spots else None

    @property
    def spots(self) -> list[ParkingSpot]:
        return list(self._spots)  # copy, not the internal list
```

**Rules of thumb:**
- Wondering whether to expose a field or write a getter? **Write the getter.**
- Returning a collection? **Return an unmodifiable view or a copy.**

---

## Abstraction

**What:** Expose only what's essential; hide implementation details behind clear interfaces. Define **what** something can do without revealing **how**.

**Why — simplification.** When payment code depends on a `PaymentMethod` interface instead of concrete `CreditCardProcessor`/`PayPalProcessor` classes, you can swap implementations without touching callers. The caller doesn't care whether you hit Stripe's API or store tokens in a DB — it calls `process()` and gets a result.

**When to introduce one:** where there's complexity — lots of variations, rules, or messy details. In interviews, look for places where logic feels tangled or requirements suggest multiple approaches; those signal that an abstraction will help.

**Bad — OrderService tightly coupled to Stripe (payment changes require modifying OrderService):**

```python
class Order:
    def __init__(self, total: float, credit_card: str):
        self.total = total
        self.credit_card = credit_card

class StripeAPI:
    def set_api_key(self, key: str) -> None: ...
    def create_charge(self, amount: float, card: str) -> None: ...

class OrderService:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def checkout(self, order: Order) -> None:
        stripe = StripeAPI()
        stripe.set_api_key(self.api_key)
        stripe.create_charge(order.total, order.credit_card)
```

**Good — depend on a PaymentMethod abstraction:**

```python
from abc import ABC, abstractmethod

class PaymentMethod(ABC):
    @abstractmethod
    def process(self, amount: float) -> bool:
        ...

class CreditCardPayment(PaymentMethod):
    def process(self, amount: float) -> bool:
        return True

class PayPalPayment(PaymentMethod):
    def process(self, amount: float) -> bool:
        return True

class OrderService:
    def __init__(self, payment_method: PaymentMethod):
        self.payment_method = payment_method

    def checkout(self, order: Order) -> None:
        self.payment_method.process(order.total)
```

The interface defines the contract (`process(amount)`); each implementation handles the details. `OrderService` doesn't care which it gets.

**Pitfall — choosing the right level of abstraction:**
- Too abstract → meaningless interfaces (`doWork()`, `handleRequest()`).
- Too specific → you haven't actually abstracted anything.
- Think about **what operations the caller needs**, not how they happen internally.

---

## Polymorphism

**What:** Replaces `if (type == "credit")` or `switch (vehicleType)` statements. Instead of checking types, call the same method and let each object handle itself — different objects respond to the same action in their own way.

Polymorphism **naturally follows from abstraction**: once you define an interface like `PaymentMethod` or `Vehicle`, each implementation provides its own behavior; the implementation that runs depends on the concrete type. No type checking required.

**Tradeoff to be ready to explain (pitfall):** highly polymorphic code can be difficult to trace and debug as implementations grow. Companies differ — some prefer explicit branches per type, others embrace the extensibility. Polymorphism gives flexibility and extensibility, but can make code flows less obvious when debugging or onboarding.

**Bad — type checks everywhere:**

```python
class ParkingLot:
    def park_vehicle(self, vehicle: Vehicle) -> bool:
        if vehicle.type == "car":
            spot = self._find_spot_by_size("regular")
            return spot is not None
        elif vehicle.type == "motorcycle":
            spot = self._find_spot_by_size("motorcycle")
            return spot is not None
        elif vehicle.type == "truck":
            spot = self._find_spot_by_size("large")
            return spot is not None
        return False
```

**Good — each vehicle type knows its own requirement:**

```python
from enum import Enum
from typing import Optional

class SpotSize(Enum):
    REGULAR = "regular"
    MOTORCYCLE = "motorcycle"
    LARGE = "large"

class Vehicle:
    def get_required_spot_size(self) -> SpotSize:
        raise NotImplementedError

class Car(Vehicle):
    def get_required_spot_size(self) -> SpotSize:
        return SpotSize.REGULAR

class Motorcycle(Vehicle):
    def get_required_spot_size(self) -> SpotSize:
        return SpotSize.MOTORCYCLE

class Truck(Vehicle):
    def get_required_spot_size(self) -> SpotSize:
        return SpotSize.LARGE

class ParkingLot:
    def park_vehicle(self, vehicle: Vehicle) -> bool:
        required = vehicle.get_required_spot_size()
        spot = self._find_spot_by_size(required)
        return spot is not None

    def _find_spot_by_size(self, size: SpotSize) -> Optional[ParkingSpot]:
        return None
```

Adding a new vehicle type = new class implementing `Vehicle`; `ParkingLot` never changes.

**When to use:** when **behavior varies by type**. Writing type checks or switch statements on an enum is the signal to use polymorphism instead.

---

## Inheritance

**What:** One class is a more specific version of another, automatically getting the parent's data and behavior. It's a tool for **sharing implementation** — but with a big cost: **tight coupling**.

**Pitfall — the "fragile base class" problem:** a subclass inherits the parent's fields and methods, so any change in the parent can break every child. Inheritance often creates more rigidity than it solves.

**Safer alternative — composition + interfaces:** an interface defines the behavior; each class implements it independently. You still get abstraction and polymorphism, without a forced parent-child relationship or shared state.

### When Inheritance Works

When there's **stable, shared implementation** multiple subclasses genuinely need. Example: bank accounts — `SavingsAccount` and `CheckingAccount` both track balances, handle deposits/withdrawals, and maintain transaction history identically.

```python
class BankAccount:
    def __init__(self):
        self.balance = 0.0

    def deposit(self, amount: float) -> None:
        self.balance += amount

    def withdraw(self, amount: float) -> bool:
        if self.balance < amount:
            return False
        self.balance -= amount
        return True

    def get_balance(self) -> float:
        return self.balance

class SavingsAccount(BankAccount):
    def __init__(self, interest_rate: float):
        super().__init__()
        self.interest_rate = interest_rate

class CheckingAccount(BankAccount):
    def __init__(self, overdraft_limit: int):
        super().__init__()
        self.overdraft_limit = overdraft_limit
```

Here the shared implementation is stable and meaningful; both subclasses genuinely *are* `BankAccount`s and don't override inherited behavior in ways that break the parent's contract.

### When Inheritance Breaks Down

**The classic interview mistake: using inheritance to model behavior differences.** If subclasses override methods with completely different implementations, you're using the wrong tool.

**Bad:**

```python
class Car:
    def start_engine(self) -> None:
        # gasoline engine start logic
        ...

class ElectricCar(Car):
    def start_engine(self) -> None:
        # electric motor startup logic - completely different
        ...
```

Electric cars don't have engines; there's no useful shared engine logic. Forcing a behavior difference into a class hierarchy creates fragile code — when you add a hybrid, do you extend `Car` or `ElectricCar`? Neither works cleanly.

**Good — isolate the varying behavior into its own abstraction and compose it:**

```python
from abc import ABC, abstractmethod

class Drivetrain(ABC):
    @abstractmethod
    def start(self) -> None:
        ...

class GasEngine(Drivetrain):
    def start(self) -> None:
        # gas engine startup logic
        ...

class ElectricMotor(Drivetrain):
    def start(self) -> None:
        # electric motor startup logic
        ...

class Car:
    def __init__(self, drivetrain: Drivetrain):
        self.drivetrain = drivetrain

    def start(self) -> None:
        self.drivetrain.start()
```

Now you can model any car without breaking the hierarchy: hybrid → give it two drivetrains; hydrogen → new `Drivetrain` implementation. `Car` never changes.

**Interview default: interfaces with composition.** Use inheritance only when you genuinely need to share stable implementation. In most LLD interviews, **you don't need inheritance at all**.

---

## Putting It Together

You don't need to recite these terms in the interview — forgetting the word "polymorphism" doesn't matter. What matters is applying them:

- **Encapsulation:** Hide state, expose behavior. Private fields, access via methods.
- **Abstraction:** Define interfaces for variations. Multiple payment methods or vehicle types? Create an interface.
- **Polymorphism:** Let objects handle themselves. No type checking, no switch statements on types.
- **Inheritance:** Compose behavior, don't inherit it. Reach for interfaces first; use inheritance only for stable shared implementation.

The concepts show through in how you design, not in what you name.
