# Good and Bad Tests

## Good Tests

**Integration-style**: Test through real interfaces, not mocks of internal parts.

```java
// GOOD: Tests observable behavior
@Test
void userCanCheckoutWithValidCart() {
    Cart cart = new Cart();
    cart.add(product);
    CheckoutResult result = checkoutService.checkout(cart, paymentMethod);
    assertEquals("confirmed", result.status());
}
```

Characteristics:

- Tests behavior users/callers care about
- Uses public API only
- Survives internal refactors
- Describes WHAT, not HOW
- One logical assertion per test

## Bad Tests

**Implementation-detail tests**: Coupled to internal structure.

```java
// BAD: Tests implementation details
@Test
void checkoutCallsInternalPaymentService() {
    PaymentService paymentService = mock(PaymentService.class);
    CheckoutService checkoutService = new CheckoutService(paymentService);

    checkoutService.checkout(cart, paymentMethod);

    verify(paymentService).process(cart.total(), paymentMethod);
}
```

Red flags:

- Mocking internal collaborators
- Testing private methods
- Asserting on call counts/order
- Test breaks when refactoring without behavior change
- Test name describes HOW not WHAT
- Verifying through external means instead of interface

```java
// BAD: Bypasses interface to verify
@Test
void createUserSavesToDatabase() throws SQLException {
    userService.createUser(new CreateUserRequest("Alice"));
    try (PreparedStatement statement = database.prepareStatement(
            "SELECT id FROM users WHERE name = ?")) {
        statement.setString(1, "Alice");
        try (ResultSet rows = statement.executeQuery()) {
            assertTrue(rows.next());
        }
    }
}

// GOOD: Verifies through interface
@Test
void createUserMakesUserRetrievable() {
    User user = userService.createUser(new CreateUserRequest("Alice"));
    User retrieved = userService.getUser(user.id());
    assertEquals("Alice", retrieved.name());
}
```

**Tautological tests**: Expected value restates the implementation, so the test passes by construction.

```java
// BAD: Expected value is recomputed the way the code computes it
@Test
void calculateTotalSumsLineItems() {
    List<LineItem> items = List.of(new LineItem(10), new LineItem(5));
    int expected = items.stream().mapToInt(LineItem::price).sum();
    assertEquals(expected, calculateTotal(items));
}

// GOOD: Expected value is an independent, known literal
@Test
void calculateTotalOfTenAndFiveIsFifteen() {
    assertEquals(15, calculateTotal(List.of(new LineItem(10), new LineItem(5))));
}
```
