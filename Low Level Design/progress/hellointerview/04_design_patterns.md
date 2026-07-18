# Design Patterns for Low-Level Design Interviews

**Source:** https://www.hellointerview.com/learn/low-level-design/in-a-hurry/patterns

## Overview

Design patterns are reusable building blocks for common design problems — **names for structures you naturally create when you follow solid design principles**.

**Reality check on the Gang of Four (1994, C++/Smalltalk, 23 patterns):** most of those patterns don't matter anymore. Modern languages replaced half with built-in features (e.g., iterators are primitives now), and the shift from inheritance-heavy OOP to composition and functional programming made others obsolete. In interviews you'll get asked about **maybe five patterns total**, not twenty-three.

**The golden rule:** only use a pattern when the problem naturally calls for it. **Forcing a pattern signals over-engineering** — the most frequent mistake. Patterns arise from good design decisions rather than driving them.

**Regional note:** In the US, most LLD interviews don't explicitly test pattern naming — you're evaluated on design quality. In other regions (particularly India), interviewers are more likely to ask about patterns directly. Be prepared for either.

Patterns fall into three categories: **creational, structural, behavioral**.

---

## Creational Patterns

Control **how objects get created**: hide construction details, allow swapping implementations, avoid tight coupling to specific classes.

### Factory Method

**What:** A helper that makes the right kind of object for you so the caller doesn't decide which one to create. Hides creation logic; keeps code flexible when the exact type can change.

**When (interview triggers):** requirements like "support different notification types" or "handle multiple payment methods." Instead of `new EmailNotification()` scattered through your code, call `notificationFactory.create(type)`. Adding SMS = updating the factory; the rest of the code never changes.

**Pitfall:** factories are polarizing — idiomatic in Java, but some engineers see them as over-engineering. If you implement one, watch your interviewer for a grimace.

```python
from abc import ABC, abstractmethod

class Notification(ABC):
    @abstractmethod
    def send(self, message: str) -> None:
        pass

class EmailNotification(Notification):
    def send(self, message: str) -> None:
        # Email sending logic
        pass

class SMSNotification(Notification):
    def send(self, message: str) -> None:
        # SMS sending logic
        pass

class NotificationFactory:
    @staticmethod
    def create(notification_type: str) -> Notification:
        if notification_type == "email":
            return EmailNotification()
        elif notification_type == "sms":
            return SMSNotification()
        raise ValueError("Unknown type")

# Usage
notif = NotificationFactory.create("email")
notif.send("Hello")
```

The factory centralizes creation logic — adding push notifications means modifying one place. Factory controls **which object gets instantiated**: it decides once and returns the right type.

**Terminology note:** this is technically **Simple Factory**, not the GoF Factory Method (which uses abstract factory classes with subclasses overriding a factory method — more complex and rarely seen in real code or interviews). Simple Factory is what people actually build and what interviewers expect when they say "use a factory."

### Builder

**What:** A helper that builds a complex object step by step without worrying about ordering or messy construction details.

**When:** an object has **many optional parts or configuration choices** — HTTP requests, database queries, configuration objects. Instead of a constructor with ten parameters (half null), build incrementally.

**Pitfalls:**
- In Python, Builder is less common — dataclasses with defaults, keyword arguments, or dictionaries are usually better; the pattern adds unnecessary complexity for most Python use cases.
- If the interviewer didn't describe a complex object with lots of optional details, **Builder probably isn't needed**. Most interview problems have simple domain objects with 2–4 required fields where a normal constructor is fine.

```python
from typing import Optional

class HttpRequest:
    def __init__(self):
        self.url: Optional[str] = None
        self.method: Optional[str] = None
        self.headers: dict[str, str] = {}
        self.body: Optional[str] = None

    class Builder:
        def __init__(self):
            self._request = HttpRequest()

        def url(self, url: str) -> 'HttpRequest.Builder':
            self._request.url = url
            return self

        def method(self, method: str) -> 'HttpRequest.Builder':
            self._request.method = method
            return self

        def header(self, key: str, value: str) -> 'HttpRequest.Builder':
            self._request.headers[key] = value
            return self

        def body(self, body: str) -> 'HttpRequest.Builder':
            self._request.body = body
            return self

        def build(self) -> 'HttpRequest':
            # Validate required fields
            if self._request.url is None:
                raise ValueError("URL is required")
            return self._request

# Usage
request = (HttpRequest.Builder()
    .url("https://api.example.com")
    .method("POST")
    .header("Content-Type", "application/json")
    .body('{"key": "value"}')
    .build())
```

Builder makes construction readable and handles optional fields cleanly. In LLD interviews it mostly appears when designing API clients or complex configurations — rarely elsewhere.

### Singleton

**What:** Ensures only one instance of a class exists. Use for exactly-one shared resources: configuration manager, connection pool, logger.

**Pitfalls (important):**
- **Most of the time you don't need one.** Pass shared objects through constructors instead — clearer and easier to test. Singletons hide dependencies and make testing harder.
- If an interviewer asks "should this be a Singleton?", **the answer is usually no** unless they explicitly want a single shared instance across the entire system.
- Thread-safe Singleton variants exist, but interviewers don't expect you to implement them in LLD interviews.
- Not idiomatic in Python: modules are only imported once, so module-level instances are natural singletons.

```python
class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def query(self, sql: str) -> None:
        # Database operations
        pass

# Usage
db = DatabaseConnection()
db.query("SELECT * FROM users")
```

---

## Structural Patterns

Deal with **how objects connect to each other** — flexible relationships without tight coupling or messy dependencies.

### Decorator

**What:** Adds behavior to an object **without changing its class**, by wrapping it. Layer on extra functionality at runtime.

**When (interview triggers):** requirements like "add logging to specific operations" or "encrypt certain messages." Keywords: **"optional features," "stack behaviors," "combine multiple enhancements."** Instead of a subclass explosion (`LoggedEmailNotification`, `EncryptedEmailNotification`, `LoggedEncryptedEmailNotification`), wrap the base object with decorators. Comes up less often than Strategy or Observer.

**Decorator vs. Subclass decision rule:**
- Behavior depends on **runtime conditions** (logging only in debug mode, caching only for certain requests) → **Decorator**.
- Behavior is a **predefined, stable type difference fixed at design time** → **Subclass**.

**Note:** this is the Decorator *design pattern*, distinct from Python's `@decorator` syntax (a language feature for function/class modification); this is an object composition pattern.

```python
from abc import ABC, abstractmethod

class DataSource(ABC):
    @abstractmethod
    def write_data(self, data: str) -> None:
        pass

    @abstractmethod
    def read_data(self) -> str:
        pass

class FileDataSource(DataSource):
    def __init__(self, filename: str):
        self.filename = filename

    def write_data(self, data: str) -> None:
        # Write to file
        pass

    def read_data(self) -> str:
        # Read from file
        return "data from file"

class EncryptionDecorator(DataSource):
    def __init__(self, source: DataSource):
        self._wrapped = source

    def write_data(self, data: str) -> None:
        encrypted = self._encrypt(data)
        self._wrapped.write_data(encrypted)  # Delegate to wrapped object

    def read_data(self) -> str:
        data = self._wrapped.read_data()
        return self._decrypt(data)

    def _encrypt(self, data: str) -> str:
        return f"encrypted:{data}"

    def _decrypt(self, data: str) -> str:
        return data.replace("encrypted:", "")

class CompressionDecorator(DataSource):
    def __init__(self, source: DataSource):
        self._wrapped = source

    def write_data(self, data: str) -> None:
        compressed = self._compress(data)
        self._wrapped.write_data(compressed)  # Delegate to wrapped object

    def read_data(self) -> str:
        data = self._wrapped.read_data()
        return self._decompress(data)

    def _compress(self, data: str) -> str:
        return f"compressed:{data}"

    def _decompress(self, data: str) -> str:
        return data.replace("compressed:", "")

# Usage
source = FileDataSource("data.txt")
source = EncryptionDecorator(source)
source = CompressionDecorator(source)
source.write_data("sensitive info")
# Data gets compressed, then encrypted, then written to file
```

Each decorator adds one piece of functionality; stack them in any order, add or remove without touching the base class or other decorators. **Caveat:** in real systems, order often affects behavior.

### Facade

**What:** A coordinator class that hides complexity behind a clean interface. **You're probably already building facades in every LLD interview without calling them that** — your `Game` class in Tic Tac Toe is a facade; any orchestrator coordinating multiple components behind a clean interface is one.

**When to name it:** almost nobody names this pattern while using it. The name matters more when wrapping existing messy code — inheriting a complex subsystem with awkward APIs and writing a facade to simplify it. In interviews, you design clean orchestrators from scratch, which is the same structure — no need to announce it.

```python
from enum import Enum

class GameState(Enum):
    IN_PROGRESS = 1
    WON = 2
    DRAW = 3

class Board:
    def place_mark(self, row: int, col: int, mark: str) -> bool:
        return True

    def check_win(self, row: int, col: int) -> bool:
        return False

    def is_full(self) -> bool:
        return False

class Player:
    def __init__(self, mark: str):
        self.mark = mark

    def get_mark(self) -> str:
        return self.mark

class Game:
    def __init__(self):
        self.board = Board()
        self.player_x = Player("X")
        self.player_o = Player("O")
        self.current_player = self.player_x
        self.state = GameState.IN_PROGRESS

    def make_move(self, row: int, col: int) -> bool:
        # Coordinates board, player, and state logic
        # Caller doesn't need to understand internal details
        if self.state != GameState.IN_PROGRESS:
            return False
        if not self.board.place_mark(row, col, self.current_player.get_mark()):
            return False

        if self.board.check_win(row, col):
            self.state = GameState.WON
        elif self.board.is_full():
            self.state = GameState.DRAW
        else:
            self.current_player = (
                self.player_o if self.current_player == self.player_x
                else self.player_x
            )
        return True

# Usage - simple interface hides all the coordination
game = Game()
game.make_move(0, 0)
game.make_move(1, 1)
```

The pattern name just describes what good orchestrator design looks like. Build it naturally; name it only if it helps communicate.

---

## Behavioral Patterns

Control **how objects interact and distribute responsibilities** — flow of control and communication between objects.

### Strategy

**What:** Replaces conditional logic with polymorphism. Use when you have **different ways of doing the same thing** and want to swap them **at runtime** (behavior chosen while the program runs, based on conditions/inputs/configuration — vs. compile time, where behavior is fixed in the class definition).

**Why interviewers love it:** the **single most common pattern in LLD interviews** — it directly tests whether you understand polymorphism and composition over inheritance. A pile of if/else or switch statements based on type = a strategy pattern waiting to happen. **If you learn one pattern, make it this one.**

```python
from abc import ABC, abstractmethod

class PaymentStrategy(ABC):
    @abstractmethod
    def pay(self, amount: float) -> bool:
        pass

class CreditCardPayment(PaymentStrategy):
    def __init__(self, card_number: str):
        self.card_number = card_number

    def pay(self, amount: float) -> bool:
        # Credit card processing logic
        print(f"Paid {amount} with credit card")
        return True

class PayPalPayment(PaymentStrategy):
    def __init__(self, email: str):
        self.email = email

    def pay(self, amount: float) -> bool:
        # PayPal processing logic
        print(f"Paid {amount} with PayPal")
        return True

class ShoppingCart:
    def __init__(self):
        self.payment_strategy = None

    def set_payment_strategy(self, strategy: PaymentStrategy) -> None:
        self.payment_strategy = strategy

    def checkout(self, amount: float) -> None:
        self.payment_strategy.pay(amount)

# Usage
cart = ShoppingCart()

cart.set_payment_strategy(CreditCardPayment("1234-5678"))
cart.checkout(100.00)

cart.set_payment_strategy(PayPalPayment("user@example.com"))
cart.checkout(50.00)
```

Instead of checkout logic full of `if payment_type == "credit"`, each payment method handles itself — polymorphism with a pattern name.

**Strategy vs. Factory:**
- **Strategy** swaps **behavior** at runtime through composition — the cart holds a strategy reference and delegates to it; it decides which behavior to use *after the object exists*.
- **Factory** decides **which type to instantiate**.

### Observer

**What:** Objects subscribe to events and get notified when something happens. Use when changes in one object must trigger updates in others.

**When (interview triggers):** a **top-tier interview pattern**. Multiple components care about state changes — a stock price changes and multiple displays update; a user places an order and inventory, notifications, and analytics all need to know. If the problem involves the words **"notify"** or **"update multiple components"**, think Observer.

```python
from abc import ABC, abstractmethod

class Observer(ABC):
    @abstractmethod
    def update(self, symbol: str, price: float) -> None:
        pass

class Subject(ABC):
    @abstractmethod
    def attach(self, observer: Observer) -> None:
        pass

    @abstractmethod
    def detach(self, observer: Observer) -> None:
        pass

    @abstractmethod
    def notify_observers(self) -> None:
        pass

class Stock(Subject):
    def __init__(self, symbol: str):
        self._observers: list[Observer] = []
        self.symbol = symbol
        self.price = 0.0

    def attach(self, observer: Observer) -> None:
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)

    def set_price(self, price: float) -> None:
        self.price = price
        self.notify_observers()  # Price changed, tell everyone

    def notify_observers(self) -> None:
        for observer in self._observers:
            observer.update(self.symbol, self.price)

class PriceDisplay(Observer):
    def update(self, symbol: str, price: float) -> None:
        print(f"Display updated: {symbol} = ${price}")

class PriceAlert(Observer):
    def __init__(self, threshold: float):
        self.threshold = threshold

    def update(self, symbol: str, price: float) -> None:
        if price > self.threshold:
            print(f"Alert! {symbol} exceeded ${self.threshold}")

# Usage
stock = Stock("AAPL")

display = PriceDisplay()
alert = PriceAlert(150.00)

stock.attach(display)
stock.attach(alert)

stock.set_price(145.00)  # Both observers get notified
stock.set_price(155.00)  # Both observers get notified
```

When the price changes, every attached observer updates automatically — the stock doesn't need to know what observers do with the information.

### State Machine (State Pattern)

**What:** Handles state transitions cleanly. Use when an object's **behavior changes based on its internal state** and transition rules are complex. Also called the "State pattern"; "state machine" is the more common term.

**When (interview triggers):** less common than Strategy/Observer, but when you need one it's usually **the centerpiece of the entire design** — the interview is probably organized around it. Shows up in vending machines, document workflows, game states. **If the word "state" appears multiple times in the requirements, you're probably looking at a state machine.** Instead of scattered conditionals checking current state everywhere, encapsulate each state's behavior in its own class.

**Interview tip:** draw a **state diagram** — states as circles, transitions as arrows labeled with actions. It makes the design immediately clear, and interviewers appreciate the visual.

```python
from abc import ABC, abstractmethod

class VendingMachineState(ABC):
    @abstractmethod
    def insert_coin(self, machine: 'VendingMachine') -> None:
        pass

    @abstractmethod
    def select_product(self, machine: 'VendingMachine') -> None:
        pass

    @abstractmethod
    def dispense(self, machine: 'VendingMachine') -> None:
        pass

class NoCoinState(VendingMachineState):
    def insert_coin(self, machine: 'VendingMachine') -> None:
        print("Coin inserted")
        machine.set_state(HasCoinState())

    def select_product(self, machine: 'VendingMachine') -> None:
        print("Insert coin first")

    def dispense(self, machine: 'VendingMachine') -> None:
        print("Insert coin first")

class HasCoinState(VendingMachineState):
    def insert_coin(self, machine: 'VendingMachine') -> None:
        print("Coin already inserted")

    def select_product(self, machine: 'VendingMachine') -> None:
        print("Product selected")
        machine.set_state(DispenseState())

    def dispense(self, machine: 'VendingMachine') -> None:
        print("Select product first")

class DispenseState(VendingMachineState):
    def insert_coin(self, machine: 'VendingMachine') -> None:
        print("Please wait, dispensing")

    def select_product(self, machine: 'VendingMachine') -> None:
        print("Please wait, dispensing")

    def dispense(self, machine: 'VendingMachine') -> None:
        print("Dispensing product")
        machine.set_state(NoCoinState())

class VendingMachine:
    def __init__(self):
        self._current_state: VendingMachineState = NoCoinState()

    def insert_coin(self) -> None:
        self._current_state.insert_coin(self)

    def select_product(self) -> None:
        self._current_state.select_product(self)

    def dispense(self) -> None:
        self._current_state.dispense(self)

    def set_state(self, state: VendingMachineState) -> None:
        self._current_state = state

# Usage
machine = VendingMachine()

machine.select_product()  # "Insert coin first"
machine.insert_coin()     # "Coin inserted"
machine.select_product()  # "Product selected"
machine.dispense()        # "Dispensing product"
```

Each state knows which state comes next and what actions are valid — no giant switch statements checking current state in every method.

---

## Wrapping Up — Cheat Sheet

Patterns only help when they match the problem. **Most interview-ready designs use no patterns, or at most one or two. Reaching for three or more probably means you're forcing it and over-engineering.**

**Creational**
- **Factory** → Callers shouldn't care which concrete class gets created.
- **Builder** → Object has lots of optional fields or messy construction.
- **Singleton** → You truly need one global instance (rare in interviews).

**Structural**
- **Decorator** → Layer optional behaviors at runtime without subclass explosion.
- **Facade** → Hide internal complexity behind a simple entry point.

**Behavioral**
- **Strategy** → Replace if/else logic with interchangeable behaviors.
- **Observer** → Multiple components need to react to a single event.
- **State Machine** → Behavior depends on current state and transitions get messy.

Focus on solving the problem cleanly; name the pattern afterward if it fits.
