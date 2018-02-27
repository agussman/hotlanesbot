import { Injectable } from '@angular/core';

@Injectable()
export class TollDataService {

  constructor() { }

  get95pins(): string {
    return "HELLO THERE FROM WITHIN THE SERVICE";
  }

}
