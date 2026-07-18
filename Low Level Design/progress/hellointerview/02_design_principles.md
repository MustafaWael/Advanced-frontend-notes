# Design Principles for Low-Level Design Interviews

**Source:** https://www.hellointerview.com/learn/low-level-design/in-a-hurry/design-principles

## Why Principles Matter

Design principles guide decision-making toward clean, extensible, maintainable code. In an LLD interview (parking lot, chess game, etc.) you constantly face calls like: Should this be a separate class? Should I use inheritance here? Is this abstraction worth it? Principles give you a framework to make those calls **and explain them**.

Don't stress over memorizing acronyms or reciting SOLID like the alphabet. **Interviewers care that you apply the lessons, not that you can name them.**

Two categories worth knowing:
1. **General software design principles**
2. **Object-oriented design principles (SOLID)** — these get more attention because most LLD problems expect class hierarchies.

---

## General Software Design Principles

If you only remember three: **KISS, DRY, YAGNI**. They carry you through most interviews.

### KISS — Keep It Simple, Stupid

The simplest solution that works is usually the right one. If a simple conditional solves the problem, don't reach for a strategy pattern. If a single class handles the job without getting messy, don't split it.

**This is the single most-violated principle in LLD interviews.** Candidates over-engineer to show off pattern knowledge — factories, builders, decorators where a basic class works. Interviewers notice. They want to see you distinguish problems needing sophisticated solutions from problems needing simple ones.

**When to add complexity:** when simplicity stops working.
- A single class grows to 500 lines with ten responsibilities → refactor.
- Adding a new payment method means modifying code in five places → introduce a strategy pattern.
- But **start simple**.

### DRY — Don't Repeat Yourself

Same logic in multiple places → pull it into one place. Three classes validating emails the same way → shared validation method. Two services converting timestamps → utility function.

**Benefit: maintenance.** When rules change or bugs appear, you fix one place instead of hunting through the codebase.

**Pitfalls / nuance:**
- Don't take DRY too far. If two pieces of code **look similar but serve different purposes**, duplication may be fine. Forcing shared code creates artificial coupling where changes to one break the other. The test: is the logic **conceptually the same**, not just textually similar?
- **DRY conflicts with KISS.** Sometimes duplicating code in two places is simpler than building an abstraction. There's no universally right answer — showing you understand the tradeoff is what separates senior candidates.

**Interview move — acknowledge both sides:**
> "I expect this validation logic to appear in multiple places, but I'm going to start by keeping it in the User class to avoid adding unnecessary complexity early. If we see it duplicated three or four times, we can pull it into a shared validator."

### YAGNI — You Aren't Gonna Need It

Build what you need **now**, not what you might need later. Designing a parking lot? Don't add valet parking or EV charging stations unless requirements mention them. Don't make classes extensible in every direction "just in case."

**Why:** you usually guess future requirements wrong. You add complexity for scenarios that never happen, and when a real requirement arrives it's different from what you prepared for — leaving you maintaining dead code.

**Nuance:** YAGNI doesn't mean "never think ahead" — it means **don't build ahead**. Design with extension in mind; implement only what's needed now.

When the interviewer asks "how would you extend this?", that's your cue to discuss how you'd modify the design if new requirements appeared — but keep the initial design to actual needs.

### Separation of Concerns

Different parts of the code handle different responsibilities and don't know each other's internals. UI shouldn't contain business logic; business logic shouldn't know how data is stored; the data layer shouldn't format strings for display.

**Bad — display, input handling, and game rules all mixed into one method:**

```python
class TicTacToe:
    def __init__(self):
        self.board = [["" for _ in range(3)] for _ in range(3)]

    def play(self):
        while True:
            # Display mixed with game logic
            for row in self.board:
                print(row)

            # Input handling mixed in
            row = int(input())
            col = int(input())
            self.board[row][col] = "X"

            # Win checking mixed in
            if (
                self.board[0][0] == self.board[1][1]
                and self.board[1][1] == self.board[2][2]
            ):
                print("Winner!")
                break
```

**Good — Board, Display, InputHandler each own their responsibility:**

```python
class TicTacToe:
    def __init__(self, board, display, input_handler):
        self.board = board
        self.display = display
        self.input_handler = input_handler

    def play(self):
        while not self.board.has_winner():
            self.display.render(self.board)
            move = self.input_handler.get_next_move()
            self.board.make_move(move)
        self.display.show_winner(self.board.get_winner())
```

**Payoff:** switching console → GUI touches only `InputHandler`; changing rendering touches only `Display`; new win conditions touch only `Board`. Each change is isolated, and each part can be tested independently.

### Law of Demeter (Principle of Least Knowledge)

A method should only talk to its immediate friends, not reach through objects into distant parts of the system.

**Violation:** `order.getCustomer().getAddress().getZipCode()`

**Problem: coupling.** Your code now knows the internal structure of three objects; if any changes its data organization, your code breaks. **Fix:** put `getCustomerZipCode()` on `Order` and let it navigate internally.

**Pitfall / clarification:** method chaining itself is not the problem. Fluent interfaces like `builder.setName("John").setAge(30).build()` are fine because they return the same object type. The issue is chaining that **leaks internal structure by traversing multiple different object types**.

**In interviews:** when defining class methods, return the specific data callers need or provide higher-level methods — don't return complex objects for callers to dig through.

---

## Object-Oriented Design Principles (SOLID)

SOLID applies when designing classes and their relationships — constant in LLD interviews.

**Context / pitfall:** SOLID comes from Java's heyday of deep inheritance and interface-heavy design. Outside Java/C#, excessive SOLID is falling out of fashion — modern languages favor composition over class hierarchies and functions over interfaces. **Don't break KISS by forcing SOLID where simpler solutions work.** Apply these when the problem calls for them; recognize when you're adding complexity for its own sake.

### SRP — Single Responsibility Principle

**A class should have one reason to change.** If it mixes concerns, split them. Foundation of good class design.

**Bad — content generation + PDF formatting + file storage in one class:**

```python
class Report:
    def generate_content(self) -> str:
        return "content"

    def print_to_pdf(self) -> None:
        # PDF formatting
        pass

    def save_to_file(self) -> None:
        # file I/O
        pass
```

**Good — split responsibilities:**

```python
class Report:
    def generate_content(self) -> str:
        return "content"

class PDFPrinter:
    def print(self, report: Report) -> None:
        # PDF formatting
        pass

class FileStorage:
    def save(self, content: str) -> None:
        # file I/O
        pass
```

PDF library changes → touch only `PDFPrinter`. Files → database → touch only `FileStorage`. Content logic changes → touch only `Report`.

### OCP — Open/Closed Principle

**Open for extension, closed for modification.** Add new behavior without changing existing code, usually via interfaces/abstract classes so new implementations don't touch the original.

**Why:** every modification of existing code risks breaking things that work. With interfaces from the start, adding functionality = writing new classes; old code never changes, so it can't break.

**Bad — every new payment type modifies this method:**

```python
class PaymentProcessor:
    def process(self, payment_type: str, amount: float) -> None:
        if payment_type == "credit":
            # credit card logic
            pass
        elif payment_type == "paypal":
            # paypal logic
            pass
        # Adding crypto means modifying this method
```

**Good — new payment types are new classes:**

```python
from abc import ABC, abstractmethod

class PaymentMethod(ABC):
    @abstractmethod
    def process(self, amount: float) -> None:
        ...

class CreditCardPayment(PaymentMethod):
    def process(self, amount: float) -> None:
        # credit card logic
        pass

class PayPalPayment(PaymentMethod):
    def process(self, amount: float) -> None:
        # paypal logic
        pass

class CryptoPayment(PaymentMethod):
    def process(self, amount: float) -> None:
        # crypto logic
        pass

class PaymentProcessor:
    def process(self, method: PaymentMethod, amount: float) -> None:
        method.process(amount)
```

Adding crypto = new `CryptoPayment` class; `PaymentProcessor` never changes.

### LSP — Liskov Substitution Principle

**Subclasses must work wherever the base class works.** A method that accepts `Bird` shouldn't break when passed a `Penguin`. Subclasses can add behavior but can't remove or break what the parent promised.

**Red flags:**
- A subclass throws an exception for a method the parent provides.
- Callers need special-case logic like `if (bird instanceof Penguin)` → you violated LSP.

**Bad — Penguin breaks the "all birds fly" expectation:**

```python
class Bird:
    def fly(self) -> None:
        # flying logic
        pass

class Penguin(Bird):
    def fly(self) -> None:
        raise NotImplementedError("Penguins can't fly")
```

**Good — separate flying into its own layer so only flyers implement it:**

```python
from abc import ABC, abstractmethod

class Bird(ABC):
    @abstractmethod
    def eat(self) -> None:
        ...

class FlyingBird(Bird):
    @abstractmethod
    def fly(self) -> None:
        ...

class Sparrow(FlyingBird):
    def eat(self) -> None:
        pass

    def fly(self) -> None:
        pass

class Penguin(Bird):
    def eat(self) -> None:
        pass
```

**In interviews:** when designing hierarchies, think carefully about which methods belong in the base class vs. subclasses.

### ISP — Interface Segregation Principle

**Prefer small, focused interfaces over large general-purpose ones.** Don't force classes to implement methods they don't need. If a class needs two methods from a ten-method interface, the interface is too big.

**Why:** fat interfaces force empty implementations or exception-throwing methods — a code smell. Split large interfaces into smaller cohesive ones; classes can implement multiple small interfaces.

**Bad:**

```python
class Worker:
    def work(self) -> None: ...
    def eat(self) -> None: ...
    def sleep(self) -> None: ...

class Robot(Worker):
    def work(self) -> None:
        pass

    def eat(self) -> None:
        # robots don't eat
        pass

    def sleep(self) -> None:
        # robots don't sleep
        pass
```

**Good:**

```python
class Workable:
    def work(self) -> None: ...

class Feedable:
    def eat(self) -> None: ...

class Restable:
    def sleep(self) -> None: ...

class Human(Workable, Feedable, Restable):
    def work(self) -> None: pass
    def eat(self) -> None: pass
    def sleep(self) -> None: pass

class Robot(Workable):
    def work(self) -> None: pass
```

### DIP — Dependency Inversion Principle

**Depend on abstractions, not concrete implementations.** Instead of `NotificationService` creating an `EmailSender` directly, it accepts a `MessageSender` interface via its constructor.

**The "inversion":** normally business logic conforms to whatever the implementation provides. DIP flips it — define an interface based on what your **business logic needs**, and make implementations conform to that. The implementation adapts to the business logic, not vice versa.

**Why it matters — testability and flexibility:** with a concrete `EmailSender` dependency you can't unit test without sending real emails, and can't swap to SMS without modifying the service. With an interface, inject a mock for tests or a different implementation for different channels.

**Bad — tightly coupled:**

```python
class EmailSender:
    def send(self, message: str) -> None:
        # send email
        pass

class NotificationService:
    def __init__(self) -> None:
        self.email_sender = EmailSender()

    def notify(self, message: str) -> None:
        self.email_sender.send(message)
```

**Good — interface + constructor injection:**

```python
from abc import ABC, abstractmethod

class MessageSender(ABC):
    @abstractmethod
    def send(self, message: str) -> None:
        ...

class EmailSender(MessageSender):
    def send(self, message: str) -> None:
        # send email
        pass

class NotificationService:
    def __init__(self, sender: MessageSender) -> None:
        self.sender = sender

    def notify(self, message: str) -> None:
        self.sender.send(message)
```

Now both high-level (`NotificationService`) and low-level (`EmailSender`) modules depend on the abstraction; neither knows about the other. Swap email for SMS by passing a different implementation; unit test with a mock.

**Terminology note:** DIP is the design **principle**; *dependency injection* (passing dependencies through the constructor) is a **technique** for achieving it. Related, not the same.

---

## Putting It All Together — Cheat Sheet

You don't need to name principles constantly. Use them to guide decisions and reference them briefly when explaining tradeoffs — tools for thinking, not a checklist to recite.

**General Principles**
- **KISS** → Start simple, add complexity only when needed
- **DRY** → Reduce duplication, simplify maintenance
- **YAGNI** → Build for today, not hypothetical futures
- **Separation of Concerns** → Enable independent testing and changes
- **Law of Demeter** → Reduce coupling, hide internal structure

**SOLID Principles**
- **SRP** → Keep classes focused on one responsibility
- **OCP** → Support future requirements without modifying existing code
- **LSP** → Prevent brittle hierarchies that break at runtime
- **ISP** → Keep interfaces clean and focused
- **DIP** → Decouple business logic from implementation details

Focus on the reasoning behind your choices — the principles will show through naturally.
