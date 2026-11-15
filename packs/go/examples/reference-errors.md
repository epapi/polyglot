---
source: go_doc
kind: reference
language: go
version: "1.26"
package: errors
url: https://pkg.go.dev/errors
license: BSD-3-Clause
---

# errors

## Overview

Package errors implements functions to manipulate errors.

The New function creates errors whose only content is a text message.

An error e wraps another error if e's type has one of the methods

```go
Unwrap() error
Unwrap() []error
```

If e.Unwrap() returns a non-nil error w or a slice containing w, then we say
that e wraps w. A nil error returned from e.Unwrap() indicates that e does
not wrap any error. It is invalid for an Unwrap method to return an []error
containing a nil error value.

An easy way to create wrapped errors is to call fmt.Errorf and apply the %w verb
to the error argument:

```go
wrapsErr := fmt.Errorf("... %w ...", ..., err, ...)
```

Successive unwrapping of an error creates a tree. The Is and As functions
inspect an error's tree by examining first the error itself followed by the tree
of each of its children in turn (pre-order, depth-first traversal).

See https://go.dev/blog/go1.13-errors for a deeper discussion of the philosophy
of wrapping and when to wrap.

### Prefer Is over equality checks

Is examines the tree of its first argument looking for an error that matches the
second. It reports whether it finds a match. It should be used in preference to
simple equality checks:

```go
if errors.Is(err, fs.ErrExist)
```

is preferable to

```go
if err == fs.ErrExist
```

because the former will succeed if err wraps io/fs.ErrExist.

### Prefer AsType over type assertions

AsType examines the tree of its argument looking for an error whose type matches
its type argument. If it succeeds, it returns the corresponding value of that
type and true. Otherwise, it returns the zero value of that type and false.
The form

```go
if perr, ok := errors.AsType[*fs.PathError](err); ok {
    fmt.Println(perr.Path)
}
```

is preferable to

```go
if perr, ok := err.(*fs.PathError); ok {
    fmt.Println(perr.Path)
}
```

because the former will succeed if err wraps an *io/fs.PathError.

## Variables

### ErrUnsupported

```go
var ErrUnsupported = New("unsupported operation")
```

ErrUnsupported indicates that a requested operation cannot be performed,
because it is unsupported. For example, a call to os.Link when using a file
system that does not support hard links.

Functions and methods should not return this error but should instead return
an error including appropriate context that satisfies

```go
errors.Is(err, errors.ErrUnsupported)
```

either by directly wrapping ErrUnsupported or by implementing an Is method.

Functions and methods should document the cases in which an error wrapping
this will be returned.

## Functions

### As

```go
func As(err error, target any) bool
```

As finds the first error in err's tree that matches target, and if one
is found, sets target to that error value and returns true. Otherwise,
it returns false.

For most uses, prefer AsType. As is equivalent to AsType but sets its target
argument rather than returning the matching error and doesn't require its
target argument to implement error.

The tree consists of err itself, followed by the errors obtained by
repeatedly calling its Unwrap() error or Unwrap() []error method. When err
wraps multiple errors, As examines err followed by a depth-first traversal
of its children.

An error matches target if the error's concrete value is assignable to
the value pointed to by target, or if the error has a method As(any) bool
such that As(target) returns true. In the latter case, the As method is
responsible for setting target.

An error type might provide an As method so it can be treated as if it were
a different error type.

As panics if target is not a non-nil pointer to either a type that
implements error, or to any interface type.

### AsType

```go
func AsType[E error](err error) (E, bool)
```

AsType finds the first error in err's tree that matches the type E, and if
one is found, returns that error value and true. Otherwise, it returns the
zero value of E and false.

The tree consists of err itself, followed by the errors obtained by
repeatedly calling its Unwrap() error or Unwrap() []error method. When
err wraps multiple errors, AsType examines err followed by a depth-first
traversal of its children.

An error err matches the type E if the type assertion err.(E) holds,
or if the error has a method As(any) bool such that err.As(target) returns
true when target is a non-nil *E. In the latter case, the As method is
responsible for setting target.

### Is

```go
func Is(err, target error) bool
```

Is reports whether any error in err's tree matches target. The target must
be comparable.

The tree consists of err itself, followed by the errors obtained by
repeatedly calling its Unwrap() error or Unwrap() []error method. When err
wraps multiple errors, Is examines err followed by a depth-first traversal
of its children.

An error is considered to match a target if it is equal to that target or if
it implements a method Is(error) bool such that Is(target) returns true.

An error type might provide an Is method so it can be treated as equivalent
to an existing error. For example, if MyError defines

```go
func (m MyError) Is(target error) bool { return target == fs.ErrExist }
```

then Is(MyError{}, fs.ErrExist) returns true. See syscall.Errno.Is for an
example in the standard library. An Is method should only shallowly compare
err and the target and not call Unwrap on either.

### Join

```go
func Join(errs ...error) error
```

Join returns an error that wraps the given errors. Any nil error values are
discarded.